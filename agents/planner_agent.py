"""
Planner Agent
Uses Ollama LLM to analyse company + product + target audience and produce a refined execution plan.
Reads target audience by product_id from state.
"""
import json
from database.sqlite_db import get_target_audience, get_company_profile, get_product_by_id, log_agent_step
from config.settings import PLANNER_TEMPERATURE
from utils.llm_utils import call_ollama, extract_json_object

PLAN_PROMPT = """You are a B2B lead generation strategist AI.

Given the company details and target audience below, produce a refined lead generation plan.

Company:
- Name: {company_name}
- Industry: {company_industry}
- Description: {company_description}

Product Being Sold:
- Name: {product_name}
- Description: {product_description}

Target Audience for this Product:
- Industry: {target_industry}
- Location: {target_location}
- Roles: {target_roles}
- Company Size: {target_size}
- Keywords: {target_keywords}
- Competitors: {target_competitors}

Return a JSON object with these fields:
{{
  "industry": "single best target industry (one value)",
  "location": "single best target location (one value)",
  "roles": ["role1", "role2", "role3"],
  "company_size": "best size range",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "competitors": ["comp1", "comp2"],
  "strategy": "2-3 sentence lead generation strategy",
  "icp": "Ideal Customer Profile description in one sentence"
}}

Return ONLY valid JSON, nothing else."""




def run_planner(state: dict) -> dict:
    run_id     = state.get("run_id", 0)
    product_id = state.get("product_id")

    log_agent_step(run_id, "PlannerAgent", f"Reading company profile, product and target audience (product_id={product_id}).")

    company = get_company_profile()
    product = get_product_by_id(product_id) if product_id else None
    target  = get_target_audience(product_id) if product_id else None

    if not target:
        log_agent_step(run_id, "PlannerAgent", "No target audience found for this product.", "ERROR")
        state["error"] = "No target audience configured for this product."
        return state

    if not product:
        log_agent_step(run_id, "PlannerAgent", "Product not found.", "ERROR")
        state["error"] = "Product not found."
        return state

    # Build base plan from DB values (fallback if LLM fails)
    base_plan = {
        "industry":       target.get("industry", "").split(",")[0].strip(),
        "location":       target.get("location", "").split(",")[0].strip(),
        "country":        target.get("country", ""),
        "business_type":  target.get("business_type", "B2B"),
        "roles":          [r.strip() for r in target.get("roles", "").split(",") if r.strip()],
        "company_size":   target.get("company_size", ""),
        "keywords":       [k.strip() for k in target.get("keywords", "").split(",") if k.strip()],
        "competitors":    [c.strip() for c in target.get("competitors", "").split(",") if c.strip()],
        "company_name":   company.get("company_name", "") if company else "",
        "product_name":   product.get("product_name", ""),
        "strategy": "",
        "icp": "",
    }

    # Send only first values to keep LLM focused
    first_industry    = target.get("industry", "").split(",")[0].strip()
    first_location    = target.get("location", "").split(",")[0].strip()
    first_roles       = ", ".join([r.strip() for r in target.get("roles", "").split(",") if r.strip()][:4])
    first_keywords    = ", ".join([k.strip() for k in target.get("keywords", "").split(",") if k.strip()][:5])
    first_competitors = ", ".join([c.strip() for c in target.get("competitors", "").split(",") if c.strip()][:3])

    log_agent_step(run_id, "PlannerAgent",
                   f"Product: '{product['product_name']}' | Industry: '{first_industry}' | Location: '{first_location}'")
    log_agent_step(run_id, "PlannerAgent", "Sending to Ollama LLM for strategic refinement...")

    prompt = PLAN_PROMPT.format(
        company_name        = company.get("company_name", "N/A") if company else "N/A",
        company_industry    = company.get("industry", "N/A") if company else "N/A",
        company_description = company.get("description", "N/A") if company else "N/A",
        product_name        = product.get("product_name", "N/A"),
        product_description = product.get("description", "N/A"),
        target_industry     = first_industry,
        target_location     = first_location,
        target_roles        = first_roles,
        target_size         = target.get("company_size", ""),
        target_keywords     = first_keywords,
        target_competitors  = first_competitors,
    )

    raw, err = call_ollama(prompt, temperature=PLANNER_TEMPERATURE, num_predict=600, timeout=60)

    if err:
        log_agent_step(run_id, "PlannerAgent", f"Ollama unavailable ({err}), using raw DB values.", "WARNING")
        state["plan"] = base_plan
        return state

    try:
        json_str = extract_json_object(raw)
        if not json_str:
            raise ValueError("No JSON object found")
        refined = json.loads(json_str)

        plan = {
            "industry":      refined.get("industry",     base_plan["industry"]),
            "location":      refined.get("location",     base_plan["location"]),
            "country":       base_plan["country"],        # always from DB, not LLM
            "business_type": base_plan["business_type"], # always from DB, not LLM
            "roles":         refined.get("roles",        base_plan["roles"]),
            "company_size":  refined.get("company_size", base_plan["company_size"]),
            "keywords":      refined.get("keywords",     base_plan["keywords"]),
            "competitors":   refined.get("competitors",  base_plan["competitors"]),
            "strategy":      refined.get("strategy",     ""),
            "icp":           refined.get("icp",          ""),
            "company_name":  base_plan["company_name"],
            "product_name":  base_plan["product_name"],
        }

        log_agent_step(run_id, "PlannerAgent", f"LLM Strategy: {plan['strategy']}")
        log_agent_step(run_id, "PlannerAgent", f"ICP: {plan['icp']}")
        log_agent_step(run_id, "PlannerAgent",
                       f"Refined — Industry: {plan['industry']}, Location: {plan['location']}, Roles: {plan['roles']}")
        state["plan"] = plan

    except Exception as e:
        log_agent_step(run_id, "PlannerAgent", f"LLM parse failed ({e}), using raw DB values.", "WARNING")
        state["plan"] = base_plan

    return state
