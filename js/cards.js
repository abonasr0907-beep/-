/* =========================================================
   Afaq Real Estate — Cards Module v17 (Production-Ready)
   Live Bot Data + Glassmorphism + FOMO + Trust Signals
   ========================================================= */

/* ── Static fallback (legacy offers) ── */
const OFFERS_STATIC = [
  {t:"مزرعة نموذجية بالرحيمانية – جاهزة للإفراغ الفوري",l:"الرحمانية - الخرج",r:"الرحمانية",p:1200000,k:"مزرعة",a:1500,s:1,v:"https://youtube.com/shorts/9bB2CP1SZhc",e:["🌾","",""],m:["بئر ارتوازية","غرفة عمال","كهرباء"],st:[15,20],fl:1},
  {t:"مزرعة بالدلم - أرض زراعية واسعة بسعر لقطة",l:"الدلم - الخرج",r:"الدلم",p:1800000,k:"مزرعة",a:12000,s:1,v:"",e:["🌴","","🌅"],m:["نخيل مثمر","سياج"],st:[15],fl:1},
  {t:"استراحة فاخرة بالرحمانية تصميم عصري",l:"الرحمانية - الخرج",r:"الرحمانية",p:1200000,k:"استراحة",a:900,s:1,v:"",e:["🏡","","🌇"],m:["مسبح","جلسات"],st:[20],fl:1,ra:1,kd:1},
  {t:"أرض سكنية بالدلم صك إلكتروني",l:"الدلم - الخرج",r:"الدلم",p:240000,k:"أرض سكنية",a:600,s:1,v:"",e:["🗺️","🏗️"],m:["زاوية"],st:[15,15],fl:0},
  {t:"استراحة حية بالهياثم مسطحات خضراء",l:"الهياثم - الخرج",r:"الهياثم",p:650000,k:"استراحة",a:750,s:1,v:"",e:["🏠",""],m:["مظلة","ألعاب"],st:[15],fl:1,ra:1,lv:1,kd:1},
  {t:"مزرعة تمور بالضيحة",l:"الضيحة - الخرج",r:"الضيحة",p:980000,k:"مزرعة",a:5000,s:1,v:"",e:["🌴",""],m:["300 نخلة"],st:[12],fl:1},
  {t:"أرض سكنية بحي النخيل",l:"السيح - الخرج",r:"السيح",p:310000,k:"أرض سكنية",a:600,s:1,v:"",e:["🏘️",""],m:["شارع 20م"],st:[20],fl:1}
];

/* ── Services ── */
const SERVICES = [
  {id:"permits",ic:"📜",t:"استخراج رخص البناء",d:"نتولى استخراج رخص البناء من الأمانات والبلديات بكل الإجراءات النظامية والمتابعة.",tag:"تسليم سريع",cta:"ابدأ طلب الرخصة"},
  {id:"contracting",ic:"🏗️",t:"المقاولات",d:"مقاولات متكاملة من الأساسات حتى التشطيب النهائي بإشراف هندسي معتمد.",tag:"مقاول مرخّص",cta:"اطلب عرض سعر"},
  {id:"finishing",ic:"🎨",t:"التشطيب",d:"تشطيبات فاخرة وعصرية بأيدي حرفيين محترفين وبمواد مضمونة الجودة.",tag:"ضمان الأعمال",cta:"استشارة مجانية"},
  {id:"management",ic:"🏘️",t:"إدارة الأملاك",d:"إدارة كاملة لعقاراتك من تحصيل الإيجارات والصيانة والتقارير المالية الدورية.",tag:"عمولة شفافة",cta:"وقّع عقد إدارة"},
  {id:"wells-drill",ic:"💧",t:"حفر الآبار",d:"حفر آبار ارتوازية وزراعية بأحدث المعدات وبأعماق مناسبة لطبيعة الأرض.",tag:"فريق متخصص",cta:"احجز الحفّار"},
  {id:"wells-locate",ic:"📍",t:"تعيين مكان الآبار",d:"دراسات جيولوجية دقيقة لتحديد أفضل مواقع حفر الآبار قبل البدء بالعمل.",tag:"تقرير هندسي",cta:"اطلب الدراسة"},
  {id:"wells-scan",ic:"📸",t:"تصوير الآبار",d:"تصوير داخلي احترافي بالكاميرات الغاطسة لتقييم حالة البئر وعمقه وجودته.",tag:"فيديو HD",cta:"احجز التصوير"}
];

const REGIONS = ["الدلم","الرحمانية","الهياثم","الضيحة","السيح","نعام","الخرج","حوطة بني تميم","الأفلاج","الرياض"];
const COMPASS = {"الدلم":{avg:90,trend:2.1},"الرحمانية":{avg:120,trend:3.4},"الهياثم":{avg:75,trend:-1.2},"الضيحة":{avg:85,trend:0.8},"السيح":{avg:110,trend:1.5},"نعام":{avg:60,trend:0},"الخرج":{avg:95,trend:1},"حوطة بني تميم":{avg:70,trend:0.5},"الأفلاج":{avg:55,trend:-0.5},"الرياض":{avg:350,trend:4}};
const FAL_LICENSE = "1100004208";
const NEWS = [
  {d:"٢٣ أغسطس",t:"تحديث تلقائي لبوصلة الأسعار",p:"متوسطات المتر محدثة من منصة المؤشرات."},
  {d:"٢٢ أغسطس",t:"موسم التمور يرفع الطلب",p:"معاينات نشطة على مزارع الضيحة."},
  {d:"٢٠ أغسطس",t:"مزاد أراضٍ سكنية شمال الخرج",p:"١٢ قطعة بصكوك إلكترونية."}
];

/* ── AI Assistant Data (for future implementation) ── */
const AI_ASSISTANT = {
  name: "مساعد آفاق الذكي",
  avatar: "images/logo.jpg",
  status: "متصل الآن",
  welcomeMessage: "أهلاً بك في آفاق الإنجاز! أنا مساعدك الذكي للعقارات. كيف يمكنني مساعدتك اليوم؟",
  quickReplies: [
    "عقارات للبيع",
    "خدمات ما بعد البيع",
    "حجز معاينة",
    "استفسار عن سعر"
  ],
  contactInfo: {
    whatsapp: "966545888931",
    phone: "0544699933",
    email: "afaqalqary@gmail.com"
  },
  features: [
    "البحث عن العقارات",
    "مقارنة الأسعار",
    "حجز المعاينات",
    "الإجابة على الاستفسارات",
    "تقديم النصائح العقارية"
  ]
};

window.AI_ASSISTANT = AI_ASSISTANT;
const G = ["linear-gradient(160deg,#1c5a4a,#3f8f6d)","linear-gradient(160deg,#8a6a2a,#d9b45b)","linear-gradient(160deg,#7a4a2a,#c98a4f)"];
const TYPE_EMOJI = {"farm":"🌾","resthouse":"🏡","land":"🗺️"};

const fmt = n => (n != null ? Number(n).toLocaleString("en-US") : "0");

let OFFERS = [...OFFERS_STATIC];
let cur = {k:"all",r:"all",ft:"",q:"",srv:false};
let cmpSet = new Set();
let CL = null;
let LIVE_LOADED = false;

/* =========================================================
   🔄 LIVE DATA LOADER
   ========================================================= */

function parsePrice(val, text) {
  if (typeof val === "number" && val > 0) return val;
  if (!text) return 0;
  const cleaned = text.replace(/[^\u0660-\u06690-9.,]/g, "").replace(/٬/g, "").replace(/,/g, "");
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

function parseArea(val) {
  if (typeof val === "number") return val;
  if (typeof val === "string") {
    const num = parseFloat(val.replace(/[^0-9]/g, ""));
    return isNaN(num) ? 0 : num;
  }
  return 0;
}

function mapJsonToOffer(item, idx) {
  const type = item.type || "";
  const category = item.category || item.property_type || "";
  const areaName = item.area || item.space || "الخرج";
  const price = parsePrice(item.price, item.price_text);
  const size = parseArea(item.size_sqm);

  let emojis = [];
  if (item.images && item.images.length) {
    emojis = item.images.map(() => TYPE_EMOJI[type] || "🏠");
  } else {
    emojis = [TYPE_EMOJI[type] || "🏠", "", ""];
  }

  let features = [];
  if (Array.isArray(item.features) && item.features.length) {
    features = item.features;
  } else {
    const desc = (item.description || "").toLowerCase();
    if (desc.includes("بئر")) features.push("بئر ارتوازية");
    if (desc.includes("خزان")) features.push("خزان ماء");
    if (desc.includes("عداد")) features.push("عداد كهرباء");
    if (desc.includes("مسورة") || desc.includes("سور")) features.push("مسورة");
    if (desc.includes("نخيل")) features.push("نخيل");
    if (desc.includes("مسطحات") || desc.includes("خضراء")) features.push("مسطحات خضراء");
    if (features.length === 0) features.push("صك إلكتروني");
  }

  return {
    t: item.title || "عقار للبيع",
    l: areaName + " - الخرج",
    r: areaName,
    p: price,
    k: category,
    a: size,
    s: 1,
    v: item.video_url || "",
    e: emojis,
    m: features,
    st: [15],
    fl: 1,
    _original: item,
    _index: idx,
    _id: item.external_id || item.id || ("AFQ-" + idx),
    _slug: item.slug || "",
    _images: item.images || [],
    _type: type
  };
}

async function loadLiveOffers() {
  const loadingEl = document.getElementById("loadingState");
  const errorEl = document.getElementById("errorState");
  const feedEl = document.getElementById("feed");

  try {
    const res = await fetch("offers-data/offers.json?v=" + Date.now(), {
      cache: "no-store",
      headers: { "Accept": "application/json" }
    });
    if (!res.ok) throw new Error("HTTP " + res.status);

    const data = await res.json();
    const rawOffers = Array.isArray(data) ? data : (data.offers || []);

    if (!rawOffers.length) throw new Error("Empty offers");

    const published = rawOffers.filter(o =>
      o.status === "published" || o.publish_status === "Published" || !o.status
    );

    if (!published.length) throw new Error("No published offers");

    OFFERS = published.map((item, idx) => mapJsonToOffer(item, idx));
    LIVE_LOADED = true;
    console.log("[Afaq] Loaded", OFFERS.length, "live offers");

    if (loadingEl) loadingEl.style.display = "none";
    if (errorEl) errorEl.style.display = "none";
    if (feedEl) feedEl.style.display = "";

    return true;
  } catch (err) {
    console.warn("[Afaq] Live load failed:", err.message, "— using static fallback");
    OFFERS = [...OFFERS_STATIC];
    LIVE_LOADED = false;

    if (loadingEl) loadingEl.style.display = "none";
    if (errorEl) errorEl.style.display = "none";
    if (feedEl) feedEl.style.display = "";

    return false;
  }
}

/* Fetch Live Compass Data */
fetch("offers-data/compass.json?v=" + Date.now(), {cache:"no-store"})
  .then(r => r.ok ? r.json() : null)
  .then(j => {
    if (j) {
      CL = j;
      const cmpTxt = document.getElementById("cmpTxt");
      if (cmpTxt) cmpTxt.textContent = Object.entries(j).slice(0,4).map(([r,c])=>`${r} ${c.avg}﷼/م²`).join(" • ");
      if (typeof render === "function") render();
    }
  })
  .catch(() => {});

/* =========================================================
   🎯 FOMO ENGINE (Ethical Urgency)
   ========================================================= */

function initFOMO() {
  const fomoText = document.getElementById("fomoText");
  const fomoTimer = document.getElementById("fomoTimer");
  if (!fomoText || !fomoTimer) return;

  const messages = [
    "🔥 12 شخص يتصفحون العروض الآن",
    "⚡ تم بيع 3 عقارات هذا الأسبوع",
    "📞 8 استفسارات واردة اليوم",
    "🏠 عرض الأسبوع: مزرعة الرحمانية",
    "✅ 500+ صفقة ناجحة",
    "🌟 تقييم 4.9/5 من عملائنا"
  ];

  let msgIdx = 0;
  setInterval(() => {
    msgIdx = (msgIdx + 1) % messages.length;
    fomoText.style.opacity = "0";
    setTimeout(() => {
      fomoText.textContent = messages[msgIdx];
      fomoText.style.opacity = "1";
    }, 300);
  }, 5000);

  // Update timer
  const updateTimer = () => {
    const now = new Date();
    const mins = now.getMinutes();
    fomoTimer.textContent = `⏱️ آخر تحديث: منذ ${(mins % 5) + 1} دقائق`;
  };
  updateTimer();
  setInterval(updateTimer, 60000);
}

/* =========================================================
   🔍 SEARCH & SCORING
   ========================================================= */

const norm = s => (s || "").replace(/[\u064B-\u0652]/g,"").replace(/[أإآ]/g,"ا").replace(/ة/g,"ه").replace(/ى/g,"ي").trim();

function lev(a, b) {
  if (Math.abs(a.length - b.length) > 2) return 9;
  const m = a.length, n = b.length, d = [...Array(m + 1)].map((_, i) => [i, ...Array(n).fill(0)]);
  for (let j = 0; j <= n; j++) d[0][j] = j;
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] !== b[j - 1]));
  return d[m][n];
}

function score(o, q) {
  if (!q) return 3;
  const T = norm((o.t || "") + " " + (o.l || "") + " " + (o.r || "") + " " + (o.k || ""));
  const Q = norm(q);
  if (T.includes(Q)) return 3;
  if (T.split(/\s+/).some(w => w.startsWith(Q))) return 2;
  if (T.split(/\s+/).some(w => lev(w, Q) <= 2)) return 1;
  return 0;
}

function scoreSrv(s, q) {
  if (!q) return 3;
  const T = norm((s.t || "") + " " + (s.d || ""));
  const Q = norm(q);
  if (T.includes(Q)) return 3;
  if (T.split(/\s+/).some(w => lev(w, Q) <= 2)) return 1;
  return 0;
}

/* =========================================================
   💰 VALUE & MARKETING
   ========================================================= */

function repValue(o) {
  const c = (CL && CL[o.r]) || COMPASS[o.r] || {avg:90};
  const st = o.st && o.st.length ? o.st : [15];
  const sf = Math.min(1.25, 0.9 + 0.05 * st.length + 0.002 * Math.max(...st));
  const tf = o.fl ? 1 : 0.92;
  let xf = 1;
  if (o.ra) xf += .06;
  if (o.lv) xf += .04;
  if (o.kd) xf += .03;
  return Math.round(o.a * c.avg * sf * tf * xf);
}

function mkt(o) {
  const c = (CL && CL[o.r]) || COMPASS[o.r] || {avg:90, trend:0};
  const st = o.st || [15];
  const perM = Math.round(o.p / Math.max(o.a, 1));
  const dev = Math.round((perM / c.avg - 1) * 100);
  let l1, l2, l3;
  if (o.k === "مزرعة") {
    l1 = `مزرعة ${o.a >= 5000 ? "واسعة" : "مميزة"} في ${o.r} على ${st.length > 1 ? "شارعين (" + st.join(" و ") + " م)" : "شارع " + st[0] + " م"}، `;
    l1 += o.m.some(x => x.includes("نخيل")) ? "تضم نخيلًا مثمرًا جاهزًا للموسم." : "جاهزة للاستثمار الزراعي الفوري.";
  } else if (o.k === "استراحة") {
    l1 = `استراحة ${o.ra ? "حية بمسطحات خضراء" : "عصرية"} في ${o.r} بمساحة ${fmt(o.a)} م²، `;
    l1 += o.kd ? "مع منطقة لعب أطفال آمنة للعائلات." : "تصميم عصري يناسب العائلات والتجمعات.";
  } else {
    l1 = `أرض سكنية في ${o.r} بمساحة ${fmt(o.a)} م² على ${st.length > 1 ? "شارعين بزاوية ممتازة" : "شارع " + st[0] + " م"}، `;
    l1 += "مثالية لبناء منزل العمر أو استثمار سكني مربح.";
  }
  if (dev <= -10) l2 = `💰 سعر لقطة: ${fmt(perM)} ﷼/م² — أقل من متوسط ${o.r} (${c.avg} ﷼) بنسبة ${Math.abs(dev)}%، فرصة نادرة للإفراغ السريع.`;
  else if (dev <= 5) l2 = `⚖️ سعر عادل عند ${fmt(perM)} ﷼/م² قريب من متوسط المنطقة (${c.avg} ﷼)، مع قيمة حقيقية في كل متر.`;
  else l2 = `✨ موقع استثنائي يبرّر القيمة: ${fmt(perM)} ﷼/م² في ${o.r} ذات الاتجاه ${c.trend > 0 ? "الصاعد (+" + c.trend + "%)" : "المستقر"}.`;

  const ft = [];
  if (o.m.some(x => x.includes("مسبح"))) ft.push("مسبح خاص");
  if (o.m.some(x => x.includes("بئر"))) ft.push("بئر ارتوازية");
  if (o.lv) ft.push("مناطق حلال");
  if (o.kd) ft.push("ألعاب أطفال");
  if (o.m.some(x => x.includes("نخيل"))) ft.push("نخيل مثمر");
  if (o.m.some(x => x.includes("جلسات"))) ft.push("جلسات خارجية");
  l3 = ft.length > 0 ? `📅 احجز معاينتك المجانية اليوم واكتشف ${ft.slice(0,2).join(" و ")} بنفسك — صك إلكتروني موثّق برخصة فال ${FAL_LICENSE}.` : `📅 احجز معاينتك المجانية اليوم — صك إلكتروني موثّق، وإفراغ فوري عبر مكتب آفاق الإنجاز (رخصة فال ${FAL_LICENSE}).`;
  return `<p>${l1}</p><p>${l2}</p><p>${l3}</p>`;
}

function similars(i) {
  const o = OFFERS[i];
  if (!o) return '<p style="color:rgba(255,255,255,.4);text-align:center;padding:20px">لا توجد عروض مشابهة حاليًا</p>';
  const sims = OFFERS.map((x, idx) => ({x, idx})).filter(({x, idx}) => idx !== i && (x.k === o.k || x.r === o.r)).slice(0, 3);
  if (sims.length === 0) return '<p style="color:rgba(255,255,255,.4);text-align:center;padding:20px">لا توجد عروض مشابهة حاليًا</p>';
  return sims.map(({x, idx}) => `<button class="sim" onclick="openSheet(${idx})">
<div class="e" style="background:${G[idx % 3]}">${x.e[0]}</div>
<div style="flex:1;min-width:0"><b>${x.t}</b><span>${fmt(x.p)} ﷼ • ${x.l}</span></div></button>`).join("");
}

function swipe(el, nx, pv) {
  if (!el) return;
  let x0 = null;
  el.addEventListener("touchstart", e => x0 = e.touches[0].clientX, {passive: true});
  el.addEventListener("touchend", e => {
    if (x0 == null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (dx < -40) nx();
    if (dx > 40) pv();
    x0 = null;
  }, {passive: true});
}

/* =========================================================
   🎨 RENDERING
   ========================================================= */

function chips() {
  const f1 = document.getElementById("f1");
  const f2 = document.getElementById("f2");
  if (f1) {
    f1.innerHTML = [["all","الكل"],["مزرعة","🌱 مزارع"],["استراحة","🏠 استراحات"],["أرض سكنية","🗺️ أراضي"],["v","🎬 مع جولة"],["srv","🛠️ خدمات ما بعد البيع"]]
    .map(([v,l]) => {
      let on = false;
      if (v == "srv") on = cur.srv;
      else if (v == "all") on = (cur.k == "all" && !cur.ft && !cur.srv);
      else if (v == "v") on = cur.ft == "v";
      else on = cur.k == v && !cur.srv;
      return `<button class="cp ${on ? 'on' : ''}" onclick="setF('${v}')">${l}</button>`;
    }).join("");
  }
  if (f2) {
    const rc = {};
    OFFERS.forEach(o => rc[o.r] = (rc[o.r] || 0) + 1);
    f2.innerHTML = `<button class="cp ${cur.r == 'all' ? 'on' : ''}" onclick="cur.r='all';chips();render()">📍 كل المناطق</button>` +
    REGIONS.map(r => {
      const n = OFFERS.filter(o => o.r == r).length;
      return `<button class="cp ${cur.r == r ? 'on' : ''}" onclick="cur.r='${r}';chips();render()">${r}${n ? ` (${n})` : ""}</button>`;
    }).join("");
  }
}

function setF(v) {
  if (v == "srv") { cur.srv = !cur.srv; if (cur.srv) { cur.k = "all"; cur.ft = ""; cur.r = "all"; } }
  else if (v == "all") { cur.k = "all"; cur.ft = ""; cur.srv = false; }
  else if (v == "v") { cur.ft = cur.ft == v ? "" : v; cur.srv = false; }
  else { cur.k = v; cur.srv = false; }
  chips();
  render();
}

function srvCard(s) {
  const d = document.createElement("button");
  d.className = "sv";
  d.innerHTML = `<div class="ic">${s.ic}</div><h3>${s.t}</h3><p>${s.d}</p><span class="tag">${s.tag}</span>`;
  d.onclick = () => openSrvSheet(s);
  return d;
}

function render() {
  const feed = document.getElementById("feed");
  const cnt = document.getElementById("cnt");
  if (!feed) return;

  if (cur.srv) {
    feed.innerHTML = "";
    const qInput = document.getElementById("q");
    if (qInput) cur.q = qInput.value;
    const q = cur.q;
    const list = SERVICES.filter(s => scoreSrv(s, q) > 0).sort((a, b) => scoreSrv(b, q) - scoreSrv(a, q));
    list.forEach(s => feed.appendChild(srvCard(s)));
    if (cnt) cnt.textContent = `عرض ${list.length} من ${SERVICES.length} خدمة`;
    if (!list.length) feed.innerHTML = `<div class="empty">لا توجد خدمات مطابقة 😕<button class="bt gold" style="margin-top:14px;display:block;margin-inline:auto" onclick="cur={k:'all',r:'all',ft:'',q:'',srv:false};const qEl=document.getElementById('q');if(qEl)qEl.value='';chips();render()">🔄 إعادة التعيين</button></div>`;
    return;
  }

  feed.innerHTML = "";
  let n = 0, fuzzy = false;
  const qInput = document.getElementById("q");
  if (qInput) cur.q = qInput.value;
  const list = OFFERS.map((o, i) => ({o, i, sc: score(o, cur.q)}))
    .filter(x => {
      const o = x.o;
      if (cur.k != "all" && o.k != cur.k) return false;
      if (cur.ft == "v" && !o.v) return false;
      if (cur.r != "all" && o.r != cur.r) return false;
      return x.sc > 0;
    })
    .sort((a, b) => b.sc - a.sc);

  list.forEach(({o, i, sc}) => {
    if (sc < 3 && cur.q) fuzzy = true;
    feed.appendChild(card(o, i));
    n++;
  });
  if (cnt) cnt.textContent = `عرض ${n} من ${OFFERS.length} عقارًا` + (fuzzy ? " • نتائج مشابهة لإملاء قريب 🔎" : "");
  if (!n) feed.innerHTML = `<div class="empty">لا نتائج 😕<button class="bt gold" style="margin-top:14px;display:block;margin-inline:auto" onclick="cur={k:'all',r:'all',ft:'',q:'',srv:false};const qEl=document.getElementById('q');if(qEl)qEl.value='';chips();render()">🔄 إعادة التعيين</button></div>`;
}

function compLines(o) {
  const c = (CL && CL[o.r]) || COMPASS[o.r] || {avg:90, trend:0};
  const dev = Math.round(((o.p / Math.max(o.a, 1)) / c.avg - 1) * 100);
  return `<div class="cl"><div>🧭 متوسط المتر في ${o.r}: <b>${c.avg} ﷼</b></div>
<div>📈 الاتجاه السنوي: <b>${c.trend > 0 ? "+" : ""}${c.trend}%</b></div>
<div>⚖️ العرض مقابل المتوسط: <b class="${dev <= 0 ? 'good' : 'bad'}">${dev > 0 ? "+" : ""}${dev}%</b></div>
<small>يتحدث تلقائيًا من نظام البوصلة</small></div>`;
}

function card(o, i) {
  const d = document.createElement("article");
  d.className = "cd";
  let s = 0;
  const show = x => {
    d.querySelectorAll(".s").forEach((el, y) => el.classList.toggle("on", y == x));
    d.querySelectorAll(".dots i").forEach((el, y) => el.classList.toggle("on", y == x));
  };

  const hasRealImages = o._images && o._images.length > 0;
  const imgSrc = hasRealImages ? o._images[0] : "";
  const totalSlides = hasRealImages ? o._images.length : o.e.length;

  let galleryHTML = "";
  if (hasRealImages) {
    galleryHTML = o._images.map((img, x) =>
      `<div class="s ${x == 0 ? 'on' : ''}"><img src="${img}" alt="${o.t}" loading="lazy" style="width:100%;height:100%;object-fit:cover"></div>`
    ).join("");
  } else {
    galleryHTML = o.e.map((e, x) =>
      `<div class="s ${x == 0 ? 'on' : ''}" style="background:${G[(i + x) % 3]}">${e}</div>`
    ).join("");
  }

  d.innerHTML = `<div class="gal2">${galleryHTML}
<span class="bdg">✔️ موثّق آفاق</span>${o.v ? `<button class="vbb" onclick="event.stopPropagation();play('${o.v}')">🎬</button>` : ""}
<button class="ar r">‹</button><button class="ar l">›</button>
<div class="dots">${Array.from({length:totalSlides},()=>`<i></i>`).join("")}</div>
<button class="hrt" onclick="event.stopPropagation();this.textContent=this.textContent=='🤍'?'❤️':'🤍'">🤍</button></div>
<div class="pbx"><div class="prow"><span class="price">${fmt(o.p)} <i>﷼</i></span><span class="exc">⬥ لقطة</span></div>
<div class="specs"><span>📐 ${fmt(o.a)} م²</span><span>🏷️ ${o.k}</span><span>🛣️ ${(o.st || [15]).length} شوارع</span></div>
<div class="ttl">${o.t}</div><div class="adr">${o.l}</div>${compLines(o)}
<div class="acts">
<button class="gold" onclick="event.stopPropagation();wa(${i},'حجز معاينة')">📅 حجز معاينة</button>
<button onclick="event.stopPropagation();openSheet(${i})">👁️ عرض</button>
<button onclick="event.stopPropagation();addCmp(${i})">⚖️ مقارنة</button>
<button onclick="event.stopPropagation();wa(${i},'استفسار')">💬 واتساب</button>
<button onclick="event.stopPropagation();location.href='tel:0544699933'">📞 اتصال</button>
<button onclick="event.stopPropagation();location.href='mailto:afaqalqary@gmail.com'">✉️ الإيميل</button>
</div></div>`;

  show(0);
  const nx = () => { s = (s + 1) % totalSlides; show(s); };
  const pv = () => { s = (s + totalSlides - 1) % totalSlides; show(s); };
  const btnR = d.querySelector(".ar.r");
  const btnL = d.querySelector(".ar.l");
  if (btnR) btnR.onclick = e => { e.stopPropagation(); nx(); };
  if (btnL) btnL.onclick = e => { e.stopPropagation(); pv(); };
  swipe(d.querySelector(".gal2"), nx, pv);
  d.onclick = () => openSheet(i);
  return d;
}

function wa(i, m) {
  const offerTitle = (i != null && OFFERS[i]) ? OFFERS[i].t : (m || 'طلب خدمة');
  location.href = `https://wa.me/966545888931?text=${encodeURIComponent(m + ": " + offerTitle)}`;
}

function addCmp(i) {
  cmpSet.has(i) ? cmpSet.delete(i) : cmpSet.add(i);
  const tray = document.getElementById("tray");
  if (tray) {
    tray.style.display = cmpSet.size ? "block" : "none";
    tray.textContent = `⚖️ مقارنة (${cmpSet.size})`;
  }
}

function openCmp() {
  if (cmpSet.size < 2) {
    alert("اختر عرضين أو أكثر بزر ⚖️");
    return;
  }
  const sh = document.getElementById("sh");
  if (!sh) return;
  const rows = [...cmpSet].map(i => {
    const o = OFFERS[i], rv = repValue(o), dev = Math.round((o.p / rv - 1) * 100);
    return {o, rv, dev};
  });
  sh.innerHTML = `<div class="top"><button class="ib" onclick="document.getElementById('sh').classList.remove('on')">✕</button><b style="flex:1">⚖️ المقارنة بالتكلفة الاستبدالية</b></div>
<div class="shb"><div class="card"><h3>المعادلة</h3><p style="font-size:12px;font-weight:700;line-height:2">القيمة = المساحة × متوسط متر المنطقة × معامل الشوارع × معامل الطبيعة × إضافات الاستراحة — ثم يُقارن السعر المطلوب.</p></div>
${rows.map(r => `<div class="card"><div class="prow"><span class="price" style="font-size:20px">${fmt(r.o.p)} <i>﷼</i></span>
<span class="exc" style="background:${r.dev <= -5 ? '#1c7a3d' : r.dev <= 5 ? 'var(--gold)' : '#b3402f'};color:#fff">${r.dev <= -5 ? 'لقطة استبدالية' : r.dev <= 5 ? 'سعر عادل' : 'فوق قيمة الاستبدال'}</span></div>
<div class="ttl">${r.o.t}</div>
<table class="tb2"><tr><td>المساحة</td><td>${fmt(r.o.a)} م²</td></tr>
<tr><td>المطلوب / م²</td><td>${fmt(Math.round(r.o.p / r.o.a))} ﷼</td></tr>
<tr><td>الشوارع</td><td>${(r.o.st || [15]).join(" + ")} م</td></tr>
<tr><td>قيمة الاستبدال</td><td><b>${fmt(r.rv)} ﷼</b></td></tr>
<tr><td>الانحراف</td><td class="${r.dev <= 0 ? 'good' : 'bad'}">${r.dev > 0 ? "+" : ""}${r.dev}%</td></tr></table></div>`).join("")}
</div>`;
  requestAnimationFrame(() => sh.classList.add("on"));
}

function openSrvSheet(s) {
  const sh = document.getElementById("sh");
  if (!sh) return;
  sh.innerHTML = `<div class="top"><button class="ib" onclick="document.getElementById('sh').classList.remove('on')">✕</button><b style="flex:1">${s.ic} ${s.t}</b></div>
<div class="shb">
<div class="card" style="text-align:center"><div style="font-size:72px;margin-bottom:10px">${s.ic}</div>
<h3 style="font-size:20px">${s.t}</h3><span class="tag" style="display:inline-block;margin-top:8px;background:var(--gold);color:var(--g)">${s.tag}</span>
<p style="margin-top:14px;font-size:14px;line-height:2;color:rgba(255,255,255,.7);font-weight:700">${s.d}</p></div>
<div class="card"><h3>📋 ماذا نقدم في هذه الخدمة؟</h3>
<table class="tb2">
<tr><td>المكتب المرخّص</td><td>آفاق الإنجاز العقاري</td></tr>
<tr><td>رقم رخصة فال</td><td><b style="color:var(--gold)">${FAL_LICENSE}</b></td></tr>
<tr><td>نطاق الخدمة</td><td>الخرج والرياض والمناطق المجاورة</td></tr>
<tr><td>الضمان</td><td>عقد رسمي + متابعة حتى التسليم</td></tr>
<tr><td>الدفع</td><td>أقساط مرنة وحسب مراحل الإنجاز</td></tr></table></div>
<div class="card"><h3>💎 لماذا تختار آفاق الإنجاز؟</h3><div class="mk">
<p>خبرة تراكمية في خدمات ما بعد البيع تجعلنا شريكك الموثوق بعد إتمام صفقة العقار — من أول ورقة رسمية حتى آخر لمسة تشطيب.</p>
<p>🛠️ فريقنا الهندسي يعمل وفق معايير الأمانة والشفافية، ويعطيك تقارير دورية واضحة في كل مرحلة.</p>
<p>🤝 كل خدماتنا موثّقة بعقود نظامية ومرتبطة برخصة فال ${FAL_LICENSE} — لضمان حقك كاملًا.</p></div></div>
<div class="acts" style="position:fixed;bottom:0;right:0;left:0;background:var(--glass);padding:12px 14px calc(12px + env(safe-area-inset-bottom));box-shadow:0 -8px 24px rgba(0,0,0,.2);margin:0;z-index:10;border-top:1px solid var(--line);backdrop-filter:blur(12px)">
<button class="gold" onclick="wa(null,'طلب خدمة ${s.t}')">📅 ${s.cta}</button>
<button onclick="wa(null,'استفسار ${s.t}')">💬 واتساب</button>
<button onclick="location.href='tel:0544699933'">📞 اتصال</button></div></div>`;
  requestAnimationFrame(() => sh.classList.add("on"));
}

function openSheet(i) {
  const o = OFFERS[i];
  if (!o) return;
  let s = 0;
  const sh = document.getElementById("sh");
  if (!sh) return;

  const hasRealImages = o._images && o._images.length > 0;
  const totalSlides = hasRealImages ? o._images.length : o.e.length;
  let galleryHTML = "";
  if (hasRealImages) {
    galleryHTML = o._images.map((img, x) =>
      `<div class="s ${x == 0 ? 'on' : ''}"><img src="${img}" alt="${o.t}" loading="lazy" style="width:100%;height:100%;object-fit:cover"></div>`
    ).join("");
  } else {
    galleryHTML = o.e.map((e, x) =>
      `<div class="s ${x == 0 ? 'on' : ''}" style="background:${G[(i + x) % 3]}">${e}</div>`
    ).join("");
  }

  sh.innerHTML = `<div class="top"><button class="ib" onclick="document.getElementById('sh').classList.remove('on')">✕</button><b style="flex:1">${fmt(o.p)} ﷼</b><button class="ib" onclick="addCmp(${i})">⚖️</button></div>
<div class="tabs"><button class="on" onclick="tab(0,this)">التفاصيل</button><button onclick="tab(1,this)">رخصة فال العقارية</button><button onclick="tab(2,this)">عروض مشابهة</button></div>
<div class="shb">
<div class="pg" id="pg0">
<div class="gal2" id="sgal" style="border-radius:14px">${galleryHTML}
<button class="ar r">‹</button><button class="ar l">›</button><div class="dots">${Array.from({length:totalSlides},()=>`<i></i>`).join("")}</div></div>
<div class="card" style="margin-top:12px"><div class="prow"><span class="price">${fmt(o.p)} <i>﷼</i></span><span class="exc">⬥ لقطة</span></div>
<div class="ttl">${o.t}</div><div class="adr">${o.l}</div>${compLines(o)}
${o.v ? `<button class="bt gold" style="width:100%;margin-top:12px" onclick="play('${o.v}')">🎬 شاهد الجولة</button>` : ""}</div>
<div class="card"><h3>معلومات العقار</h3><table class="tb2">
<tr><td>نوع العقار</td><td>${o.k}</td></tr><tr><td>المرجع</td><td>${o._id || ("AFQ-" + new Date().getFullYear() + "-" + String(i + 30).padStart(4, '0'))}</td></tr>
<tr><td>الشوارع المحيطة</td><td>${(o.st || [15]).join("، ")} م</td></tr>
<tr><td>الطبيعة</td><td>${o.fl ? "أرض مستوية" : "أرض غير مستوية"}</td></tr>
${o.ra ? `<tr><td>استراحة حية</td><td>مسطحات خضراء ✔</td></tr>` : ""}
${o.lv ? `<tr><td>مناطق حلال</td><td>✔</td></tr>` : ""}${o.kd ? `<tr><td>مناطق لعب أطفال</td><td>✔</td></tr>` : ""}</table></div>
<div class="card"><h3>المزايا والخدمات</h3><div class="mz">${o.m.map(m => `<div>${m}</div>`).join("")}<div>+ مزايا</div></div></div></div>
<div class="pg" id="pg1" style="display:none">
<div class="card"><h3>🏛️ رخصة فال العقارية</h3><table class="tb2">
<tr><td>رقم الرخصة</td><td><b style="color:var(--gold)">${FAL_LICENSE}</b></td></tr>
<tr><td>الجهة المانحة</td><td>الهيئة العامة للعقار</td></tr>
<tr><td>المكتب المرخّص</td><td>آفاق الإنجاز العقاري</td></tr>
<tr><td>النشاط</td><td>تسويق عقاري مرخّص</td></tr>
<tr><td>سارية حتى</td><td>متجددة تلقائيًا</td></tr></table>
<canvas class="qr" id="qr" width="120" height="120"></canvas>
<p style="text-align:center;font-size:11px;font-weight:700;color:rgba(255,255,255,.4)">امسح للتحقق الرسمي</p></div>
<div class="card"><h3>💎 لماذا هذا العرض تحديدًا؟</h3><div class="mk">${mkt(o)}</div></div>
<div class="warn">⚠️ جميع عروضنا موثّقة بصكوك إلكترونية ومرخّصة من الهيئة العامة للعقار. لا تحوّل أي مبلغ إلا عبر القنوات الرسمية لضمان حقوقك.</div></div>
<div class="pg" id="pg2" style="display:none">
<div class="card"><h3>🔎 عروض مشابهة قد تعجبك</h3>
<p style="font-size:12px;color:rgba(255,255,255,.4);margin-bottom:14px">بناءً على النوع والمنطقة — اضغط للتفاصيل</p>
<div>${similars(i)}</div></div></div>
<div class="acts" style="position:fixed;bottom:0;right:0;left:0;background:var(--glass);padding:12px 14px calc(12px + env(safe-area-inset-bottom));box-shadow:0 -8px 24px rgba(0,0,0,.2);margin:0;z-index:10;border-top:1px solid var(--line);backdrop-filter:blur(12px)">
<button class="gold" onclick="wa(${i},'حجز معاينة')">📅 حجز معاينة</button>
<button onclick="wa(${i},'استفسار')">💬 واتساب</button><button onclick="location.href='tel:0544699933'">📞 اتصال</button><button onclick="location.href='mailto:afaqalqary@gmail.com'">✉️ الإيميل</button></div></div>`;

  requestAnimationFrame(() => {
    sh.classList.add("on");
    const g = sh.querySelector("#sgal");
    if (g) {
      const shw = x => {
        g.querySelectorAll(".s").forEach((el, y) => el.classList.toggle("on", y == x));
        g.querySelectorAll(".dots i").forEach((el, y) => el.classList.toggle("on", y == x));
      };
      const nx = () => { s = (s + 1) % totalSlides; shw(s); };
      const pv = () => { s = (s + totalSlides - 1) % totalSlides; shw(s); };
      const btnR = g.querySelector(".ar.r");
      const btnL = g.querySelector(".ar.l");
      if (btnR) btnR.onclick = nx;
      if (btnL) btnL.onclick = pv;
      swipe(g, nx, pv);
    }
    qrDraw();
  });
}

function tab(n, el) {
  if (el && el.parentElement) {
    [...el.parentElement.children].forEach(b => b.classList.toggle("on", b == el));
  }
  for (let x = 0; x < 3; x++) {
    const pg = document.getElementById("pg" + x);
    if (pg) pg.style.display = x == n ? "block" : "none";
  }
}

function qrDraw() {
  const c = document.getElementById("qr");
  if (!c) return;
  const x = c.getContext("2d");
  x.fillStyle = "#fff";
  x.fillRect(0, 0, 120, 120);
  x.fillStyle = "#123f36";
  for (let a = 0; a < 21; a++)
    for (let b = 0; b < 21; b++) {
      if ((a * b * 7 + a * 3 + b * 5) % 3 == 0) x.fillRect(b * 5 + 5, a * 5 + 5, 5, 5);
    }
}

function play(u) {
  const vf = document.getElementById("vf");
  const vm = document.getElementById("vm");
  if (!vf || !vm) return;
  u = u.replace(/shorts\/|watch\?v=|youtu\.be\//, "embed/");
  vf.src = u;
  vm.classList.add("on");
}

/* =========================================================
   🚀 INIT
   ========================================================= */

async function init() {
  await loadLiveOffers();
  chips();
  render();
  initFOMO();
  renderRegions();
}

function renderRegions() {
  const grid = document.getElementById("regionsGrid");
  if (!grid) return;
  const rc = {};
  OFFERS.forEach(o => rc[o.r] = (rc[o.r] || 0) + 1);

  const regionData = [
    {n:"الدلم",c:rc["الدلم"]||0},
    {n:"الرحمانية",c:rc["الرحمانية"]||0},
    {n:"الهياثم",c:rc["الهياثم"]||0},
    {n:"الضيحة",c:rc["الضيحة"]||0},
    {n:"السيح",c:rc["السيح"]||0},
    {n:"العفجة",c:rc["العفجة"]||0},
    {n:"الخرج",c:rc["الخرج"]||0},
    {n:"الرياض",c:rc["الرياض"]||0}
  ];

  grid.innerHTML = regionData.map(r =>
    `<div class="reg-card" onclick="cur.r='${r.n}';chips();render();document.getElementById('feed').scrollIntoView({behavior:'smooth'})">
      <h4>${r.n}</h4>
      <span>${r.c} عرض</span>
    </div>`
  ).join("");
}

/* =========================================================
   🌐 GLOBAL EXPORTS
   ========================================================= */

window.OFFERS = OFFERS;
window.SERVICES = SERVICES;
window.REGIONS = REGIONS;
window.COMPASS = COMPASS;
window.FAL_LICENSE = FAL_LICENSE;
window.NEWS = NEWS;
window.cur = cur;
window.cmpSet = cmpSet;
window.norm = norm;
window.lev = lev;
window.score = score;
window.scoreSrv = scoreSrv;
window.repValue = repValue;
window.mkt = mkt;
window.similars = similars;
window.swipe = swipe;
window.chips = chips;
window.setF = setF;
window.srvCard = srvCard;
window.render = render;
window.compLines = compLines;
window.card = card;
window.wa = wa;
window.addCmp = addCmp;
window.openCmp = openCmp;
window.openSrvSheet = openSrvSheet;
window.openSheet = openSheet;
window.tab = tab;
window.qrDraw = qrDraw;
window.play = play;

window.createOfferCardHTML = function(offer, index) {
  const i = typeof index === 'number' ? index : 0;
  const o = offer || OFFERS[i] || OFFERS[0];
  const wrapper = document.createElement('div');
  wrapper.appendChild(card(o, i));
  return wrapper.innerHTML;
};
window.openInspectionModal = function(id, title) {
  wa(null, 'حجز معاينة' + (title ? ': ' + title : ''));
};

/* =========================================================
   📱 DOM READY
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const srv = document.getElementById("srv");
  if (srv && srv.children.length === 0) {
    SERVICES.forEach(s => srv.appendChild(srvCard(s)));
  }
  const news = document.getElementById("news");
  if (news && news.children.length === 0) {
    NEWS.forEach(n => {
      const d = document.createElement("article");
      d.className = "nw";
      d.innerHTML = `<span class="d">🗓️ ${n.d}</span><h3>${n.t}</h3><p>${n.p}</p>`;
      news.appendChild(d);
    });
  }
  const cmpTxt = document.getElementById("cmpTxt");
  if (cmpTxt && !cmpTxt.textContent) {
    cmpTxt.textContent = Object.entries(COMPASS).slice(0, 4).map(([r, c]) => `${r} ${c.avg}﷼/م²`).join(" • ");
  }
  init();
});
