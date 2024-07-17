import time

from apify_client import ApifyClient
from srai_core.tools_env import get_string_from_env


def get_site_content(api_token, actor_id, start_url, run_id):
    client = ApifyClient(api_token)
    if run_id is None:
        # Initialize the ApifyClient with your API token

        # Prepare the actor input
        actor_input = {"startUrls": [{"url": start_url}]}

        # Start the actor and get the run object
        run = client.actor(actor_id).call(run_input=actor_input)
        if run is None:
            raise RuntimeError("Failed to start actor run!")
        run_id = run["id"]
    print(run_id)
    print(f"Started actor run with ID: {run_id}")

    # Poll the actor run status until it finishes
    while True:
        run_details = client.run(run_id).get()
        if run_details is None:
            raise RuntimeError("Actor run not found!")
        if run_details["status"] == "SUCCEEDED":
            print("Actor run succeeded!")
            break
        elif run_details["status"] == "FAILED":
            raise RuntimeError("Actor run failed!")
        else:
            print("Actor run in progress...")
        time.sleep(5)

    # Get the results of the actor run

    return client.dataset(run_details["defaultDatasetId"]).list_items().items


if __name__ == "__main__":
    APIFY_API_TOKEN = get_string_from_env("APIFY_API_KEY")
    APIFY_ACTOR_ID = "apify/website-content-crawler"  # Example actor ID, change if needed

    start_url = "https://www.crunchbase.com/organization/timbukdo-technologies"
    # https://www.crunchbase.com/organization/timbukdo-technologies/company_financials
    actor_run = "CpOkj6t25CZ11Np7j"
    list_item = get_site_content(APIFY_API_TOKEN, APIFY_ACTOR_ID, start_url, actor_run)
    print(len(list_item))
    for item in list_item:
        print(item)
