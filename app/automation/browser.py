from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from datetime import datetime
import logging
import urllib.parse
import json

logger = logging.getLogger(__name__)

# LinkedIn time filter URL codes
TIME_FILTER_MAP = {
    "any": "",
    "r86400": "r86400",    # Past 24 hours
    "r259200": "r259200",  # Past 3 days
    "r604800": "r604800",  # Past week
    "r2592000": "r2592000" # Past month
}

class BrowserAutomation:

    async def _complete_easy_apply(self, page, user) -> bool:
        """
        Walks through the multi-step LinkedIn Easy Apply modal and submits.
        Returns True if submit was successful, False otherwise.
        """
        MAX_STEPS = 10  # Safety cap for modal steps
        for step in range(MAX_STEPS):
            await asyncio.sleep(1.5)

            # Pre-fill visible text fields using user profile data
            if user and user.profile:
                full_name = user.profile.full_name or ""
                name_parts = full_name.strip().split(" ", 1)
                first = name_parts[0] if name_parts else ""
                last = name_parts[1] if len(name_parts) > 1 else ""

                for fname_sel in ["input[id*='firstName']", "input[name='firstName']", "input[autocomplete='given-name']"]:
                    el = await page.query_selector(fname_sel)
                    if el and first and not await el.input_value():
                        await el.fill(first)
                        break

                for lname_sel in ["input[id*='lastName']", "input[name='lastName']", "input[autocomplete='family-name']"]:
                    el = await page.query_selector(lname_sel)
                    if el and last and not await el.input_value():
                        await el.fill(last)
                        break

                # Phone number (if there's a field)
                phone_el = await page.query_selector("input[id*='phone']")
                if phone_el:
                    current_val = await phone_el.input_value()
                    if not current_val:
                        await phone_el.fill("0000000000")  # placeholder

            # Check for a Submit button
            submit_btn = await page.query_selector(
                "button[aria-label='Submit application'], "
                "button[data-control-name='submit_unify']"
            )
            if submit_btn:
                logger.info(f"Found Submit button at step {step+1} — clicking to submit application")
                await submit_btn.click()
                await asyncio.sleep(2)
                # Dismiss success confirmation dialog if present
                dismiss = await page.query_selector("button[aria-label='Dismiss'], button.artdeco-modal__dismiss")
                if dismiss:
                    await dismiss.click()
                logger.info("Application submitted successfully!")
                return True

            # Check for a "Next" or "Review" or "Continue" button
            next_btn = await page.query_selector(
                "button[aria-label='Continue to next step'], "
                "button[aria-label='Review your application'], "
                "button[data-control-name='continue_unify'], "
                "button[data-easy-apply-next-button]"
            )
            if next_btn:
                logger.info(f"Advancing Easy Apply step {step+1}")
                await next_btn.click()
                continue

            # Modal may have closed — check
            modal_visible = await page.query_selector(".jobs-easy-apply-modal, [data-test-modal-id='easy-apply-modal']")
            if not modal_visible:
                logger.info("Easy Apply modal closed — assuming completed.")
                return True

            # No next or submit found — bail
            logger.warning(f"No actionable button found at step {step+1}, stopping")
            break

        return False

    async def run_apply_flow(self, job_data: dict, user=None):
        title = job_data.get("title", "")
        location = job_data.get("location", "")
        keywords = job_data.get("keywords", [])
        time_filter = job_data.get("time_filter", "any")
        max_applications = int(job_data.get("max_applications", 5))

        # Build the LinkedIn job search URL
        search_query = f"{title} {' '.join(keywords[:3])}".strip() if keywords else title
        encoded_query = urllib.parse.quote(search_query)
        encoded_location = urllib.parse.quote(location)

        linkedin_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={encoded_query}"
            f"&location={encoded_location}"
            f"&f_LF=f_AL"  # Easy Apply filter
        )
        tf = TIME_FILTER_MAP.get(time_filter, "")
        if tf:
            linkedin_url += f"&f_TPR={tf}"

        logger.info(f"LinkedIn search URL: {linkedin_url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage"
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )

            # Inject LinkedIn session cookie
            li_at_cookie = None
            if user and user.profile and user.profile.linkedin_cookie:
                li_at_cookie = user.profile.linkedin_cookie.strip()

            if li_at_cookie:
                await context.add_cookies([{
                    "name": "li_at",
                    "value": li_at_cookie,
                    "domain": ".linkedin.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "None"
                }])
                logger.info("LinkedIn li_at session cookie injected")
            else:
                logger.warning("No LinkedIn cookie found — running unauthenticated")

            page = await context.new_page()
            link_opened_at = None
            screenshot_path = f"/tmp/{job_data.get('id')}_result.png"
            applied_count = 0
            errors = []
            applied_jobs_details = []

            try:
                await page.goto(linkedin_url, wait_until="domcontentloaded", timeout=30000)
                link_opened_at = datetime.utcnow()

                # Wait for job listings to load
                try:
                    await page.wait_for_selector(
                        ".jobs-search__results-list li, .base-card, .job-card-container",
                        timeout=15000
                    )
                except PlaywrightTimeout:
                    await page.screenshot(path=screenshot_path)
                    return {
                        "status": "failed",
                        "error": "LinkedIn job listings did not load. Please review your session cookie.",
                        "link_opened_at": link_opened_at,
                        "screenshot": screenshot_path
                    }

                # CRITICAL FIX: Scroll the left pane to lazy-load more jobs for max_applications
                left_pane = await page.query_selector(".jobs-search__results-list, .jobs-search-results-list")
                if left_pane:
                    scroll_attempts = max(1, max_applications // 5 + 1)
                    for _ in range(scroll_attempts):
                        await left_pane.evaluate("el => el.scrollBy(0, el.scrollHeight)")
                        await asyncio.sleep(1.2)

                job_cards = await page.query_selector_all(".jobs-search__results-list li, .base-card")
                logger.info(f"Loaded {len(job_cards)} job cards after scrolling")

                if len(job_cards) == 0:
                    return {
                        "status": "completed",
                        "message": "No Easy Apply jobs found. Try different keywords.",
                        "link_opened_at": link_opened_at
                    }

                for i, card in enumerate(job_cards):
                    if applied_count >= max_applications:
                        logger.info(f"Reached max limit ({max_applications})")
                        break
                    
                    try:
                        await card.scroll_into_view_if_needed()
                        await card.click()
                        await asyncio.sleep(2) # Give right pane time to load
                        
                        # Extract Details
                        job_title = f"Unknown Role #{i+1}"
                        company_name = "Unknown Company"
                        job_link = ""
                        
                        try:
                            title_el = await card.query_selector(".job-card-list__title, .base-search-card__title, .job-card-container__title")
                            if title_el:
                                job_title = (await title_el.inner_text()).strip()
                                job_link_raw = await title_el.get_attribute("href")
                                if job_link_raw:
                                    # clean tracking query params from link
                                    job_link = job_link_raw.split("?")[0]
                                    
                            company_el = await card.query_selector(".job-card-container__primary-description, .base-search-card__subtitle, .artdeco-entity-lockup__subtitle")
                            if company_el:
                                company_name = (await company_el.inner_text()).strip()
                        except Exception as e:
                            logger.warning(f"Failed to parse card details: {e}")

                        easy_apply_btn = await page.query_selector(
                            "button.jobs-apply-button, "
                            ".jobs-s-apply button, "
                            "button[aria-label*='Easy Apply'], "
                            ".jobs-apply-button--top-card"
                        )
                        if not easy_apply_btn:
                            continue

                        btn_text = await easy_apply_btn.inner_text()
                        if "easy apply" not in btn_text.lower():
                            continue

                        logger.info(f"Clicking Easy Apply for: {company_name} - {job_title}")
                        await easy_apply_btn.click()
                        await asyncio.sleep(1.5)

                        try:
                            await page.wait_for_selector(".jobs-easy-apply-modal, [data-test-modal-id='easy-apply-modal']", timeout=6000)
                        except PlaywrightTimeout:
                            errors.append(f"{company_name}: Easy Apply modal failed to open")
                            continue

                        submitted = await self._complete_easy_apply(page, user)
                        if submitted:
                            applied_count += 1
                            logger.info(f"Success! ({applied_count}/{max_applications}) {company_name}")
                            applied_jobs_details.append({
                                "company": company_name,
                                "title": job_title,
                                "link": job_link
                            })
                        else:
                            errors.append(f"{company_name}: Could not complete modal steps")

                    except Exception as card_err:
                        logger.warning(f"Error on job #{i+1}: {card_err}")
                        errors.append(f"Job #{i+1}: inner loop error")
                        # Emergency modal close
                        for sel in ["button[aria-label='Dismiss']", "button.artdeco-modal__dismiss"]:
                            try:
                                btn = await page.query_selector(sel)
                                if btn:
                                    await btn.click()
                                    break
                            except Exception:
                                pass
                        continue

                await page.screenshot(path=screenshot_path)

                if applied_count > 0:
                    status = "success"
                    msg = f"Successfully submitted {applied_count} application(s)."
                else:
                    status = "completed"
                    msg = "Search complete. No applications were submitted."

                return {
                    "status": status,
                    "screenshot": screenshot_path,
                    "message": msg,
                    "link_opened_at": link_opened_at,
                    "applied_at": datetime.utcnow() if applied_count > 0 else None,
                    "error": "; ".join(errors) if errors else None,
                    "applied_jobs_details": json.dumps(applied_jobs_details) # Returning serialized JSON to worker
                }

            except Exception as e:
                logger.error(f"Playwright crash: {e}", exc_info=True)
                return {
                    "status": "failed",
                    "error": str(e),
                    "link_opened_at": link_opened_at,
                    "screenshot": screenshot_path
                }
            finally:
                await browser.close()
