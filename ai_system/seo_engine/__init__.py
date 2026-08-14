#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_system.seo_engine — محرك SEO للمرحلة الثالثة
====================================================
يوفّر:
  - schema_generator: مولّد بيانات منظّمة JSON-LD (Schema.org)
  - meta_generator: مولّد وسوم HTML الميتا (title/description/og/twitter/canonical/keywords)
  - sitemap_updater: تحديث sitemap.xml (إضافة فقط — add-only)
  - indexnow: إرسال تنبيه فوري لمحركات البحث عند نشر عرض جديد
  - reviews: جمع وعرض المراجعات الشرعية فقط

كل الدوال idempotent: يمكن استدعاؤها بأمان عدة مرات دون تكرار أو تكرار.
"""

from .schema_generator import (
    generate_organization_schema,
    generate_real_estate_agent_schema,
    generate_listing_schema,
    generate_offer_schema,
    generate_image_object_schema,
    generate_breadcrumb_schema,
    generate_faq_schema,
    generate_article_schema,
    generate_property_page_schemas,
    generate_home_page_schemas,
    schemas_to_jsonld_scripts,
)
from .meta_generator import (
    generate_meta_tags,
    meta_tags_to_html,
    generate_alt_text,
)
from .sitemap_updater import (
    update_sitemap_add_only,
    verify_sitemap_integrity,
)
from .indexnow import (
    get_or_create_key,
    submit_urls,
    submit_single_url,
    submit_offer,
    get_log_summary,
)
from .reviews import (
    add_review,
    approve_review,
    reject_review,
    get_approved_reviews,
    get_pending_reviews,
    calculate_aggregate_rating,
    generate_review_schema,
    get_reviews_for_schema,
)

__all__ = [
    # schema_generator
    "generate_organization_schema",
    "generate_real_estate_agent_schema",
    "generate_listing_schema",
    "generate_offer_schema",
    "generate_image_object_schema",
    "generate_breadcrumb_schema",
    "generate_faq_schema",
    "generate_article_schema",
    "generate_property_page_schemas",
    "generate_home_page_schemas",
    "schemas_to_jsonld_scripts",
    # meta_generator
    "generate_meta_tags",
    "meta_tags_to_html",
    "generate_alt_text",
    # sitemap_updater
    "update_sitemap_add_only",
    "verify_sitemap_integrity",
    # indexnow
    "get_or_create_key",
    "submit_urls",
    "submit_single_url",
    "submit_offer",
    "get_log_summary",
    # reviews
    "add_review",
    "approve_review",
    "reject_review",
    "get_approved_reviews",
    "get_pending_reviews",
    "calculate_aggregate_rating",
    "generate_review_schema",
    "get_reviews_for_schema",
]
