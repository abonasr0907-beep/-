#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
طابور العمليات الثقيلة (Task Queue)
يعالج العمليات الثقيلة بشكل غير متزامن في الخلفية:
- رفع الصور إلى GitHub
- مزامنة العروض
- تحديث الموقع

المميزات:
- طابور asyncio.Queue
- عامل (worker) واحد يعالج المهام بالتتابع
- تتبع الإحصائيات (منجزة، فاشلة، في الانتظار)
- سجل آخر المهام
"""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger("afaq_bot.task_queue")

# ============================================================
#  الحالة العامة
# ============================================================
_queue = None           # asyncio.Queue
_worker_task = None     # asyncio.Task
_running = False

# إحصائيات
_stats = {
    "total_tasks": 0,
    "completed": 0,
    "failed": 0,
    "queue_size": 0,
}

# سجل آخر المهام (آخر 50)
_recent_tasks = []


# ============================================================
#  تعريف المهمة
# ============================================================
class Task:
    """مهمة في الطابور"""

    def __init__(self, name: str, func, *args, **kwargs):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.started_at = None
        self.completed_at = None
        self.status = "pending"  # pending, running, completed, failed
        self.error = None

    async def execute(self):
        """تنفيذ المهمة"""
        self.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = "running"
        try:
            result = self.func(*self.args, **self.kwargs)
            # إذا كانت النتيجة كوروتين، انتظرها
            if asyncio.iscoroutine(result):
                result = await result
            self.status = "completed"
            self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True, result
        except Exception as e:
            self.status = "failed"
            self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.error = str(e)[:200]
            logger.error(f"❌ فشلت المهمة '{self.name}': {e}")
            return False, str(e)


# ============================================================
#  الطابور
# ============================================================
async def start_worker():
    """بدء عامل الطابور (يُستدعى مرة واحدة عند تشغيل البوت)"""
    global _queue, _worker_task, _running
    if _running:
        return
    _queue = asyncio.Queue()
    _running = True
    _worker_task = asyncio.create_task(_worker_loop())
    logger.info("🔄 تم تشغيل طابور العمليات الثقيلة")


async def _worker_loop():
    """حلقة العامل — تعالج المهام بالتتابع"""
    global _stats
    logger.info("  ▶️ عامل الطابور يعمل...")
    while _running:
        try:
            task = await _queue.get()
            _stats["queue_size"] = _queue.qsize()
            logger.info(f"  ⏳ بدء المهمة: {task.name}")
            success, result = await task.execute()
            if success:
                _stats["completed"] += 1
                logger.info(f"  ✅ اكتملت المهمة: {task.name}")
            else:
                _stats["failed"] += 1
                logger.warning(f"  ❌ فشلت المهمة: {task.name}: {result}")
            # إضافة للسجل الأخير
            _recent_tasks.append({
                "name": task.name,
                "status": task.status,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "error": task.error,
            })
            # الاحتفاظ بآخر 50 مهمة
            if len(_recent_tasks) > 50:
                _recent_tasks[:] = _recent_tasks[-50:]
            _stats["queue_size"] = _queue.qsize()
            _queue.task_done()
        except asyncio.CancelledError:
            logger.info("  ⏹️ تم إيقاف عامل الطابور")
            break
        except Exception as e:
            logger.error(f"  ❌ خطأ في حلقة العامل: {e}")
            _stats["failed"] += 1
            await asyncio.sleep(1)  # تجنب الحلقة اللانهائية عند الخطأ


async def enqueue(name: str, func, *args, **kwargs):
    """
    إضافة مهمة إلى الطابور.
    func يمكن أن تكون دالة عادية أو async (coroutine).
    """
    global _stats
    if not _running or _queue is None:
        logger.warning(f"⚠️ الطابور غير مشتغل — تنفيذ المهمة '{name}' مباشرة")
        task = Task(name, func, *args, **kwargs)
        success, result = await task.execute()
        _recent_tasks.append({
            "name": task.name,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "error": task.error,
        })
        if len(_recent_tasks) > 50:
            _recent_tasks[:] = _recent_tasks[-50:]
        _stats["total_tasks"] += 1
        if success:
            _stats["completed"] += 1
        else:
            _stats["failed"] += 1
        return success

    task = Task(name, func, *args, **kwargs)
    await _queue.put(task)
    _stats["total_tasks"] += 1
    _stats["queue_size"] = _queue.qsize()
    logger.info(f"  📥 تمت إضافة مهمة للطابور: {name} (في الانتظار: {_stats['queue_size']})")
    return True


def enqueue_sync(name: str, func, *args, **kwargs):
    """
    إضافة مهمة للطابور من سياق متزامن (non-async).
    يستخدم asyncio.create_task داخلياً.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(enqueue(name, func, *args, **kwargs))
        else:
            logger.warning(f"⚠️ لا يوجد event loop — تنفيذ '{name}' مباشرة")
            func(*args, **kwargs)
    except RuntimeError:
        logger.warning(f"⚠️ لا يوجد event loop — تنفيذ '{name}' مباشرة")
        func(*args, **kwargs)


async def stop_worker():
    """إيقاف عامل الطابور"""
    global _running, _worker_task
    _running = False
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    logger.info("⏹️ تم إيقاف طابور العمليات")


# ============================================================
#  الإحصائيات
# ============================================================
def get_stats() -> dict:
    """جلب إحصائيات الطابور"""
    stats = dict(_stats)
    stats["recent"] = _recent_tasks[-10:][::-1]  # آخر 10 (الأحدث أولاً)
    return stats


def get_queue_size() -> int:
    """حجم الطابور الحالي"""
    return _stats.get("queue_size", 0)


def is_running() -> bool:
    """هل العامل يعمل؟"""
    return _running
