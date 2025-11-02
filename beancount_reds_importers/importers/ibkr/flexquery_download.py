#!/usr/bin/env python3
"""IBKR Flex Query Downloader"""

import sys
import time

import click
import requests


@click.command()
@click.argument("token", required=True)
@click.argument("query_id", required=True)
def flexquery_download(token, query_id):
    url = (
        "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest"
    )

    # Request Flex Query
    request_payload = {"v": "3", "t": token, "q": query_id}

    response = requests.post(url, data=request_payload)

    if response.status_code == 200:
        request_id = response.text.split("<ReferenceCode>")[1].split("</ReferenceCode>")[0]
        # print(f"Request ID: {request_id}")

        # Construct URL to get the query result
        result_url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?q={request_id}&t={token}&v=3"

        # Try up to 10 times (roughly 100 seconds total)
        for attempt in range(10):
            result_response = requests.get(result_url)
            if result_response.status_code == 200:
                text = result_response.text
                if "Statement generation in progress" in text:
                    print(
                        "Statement generation in progress, waiting 10 seconds...", file=sys.stderr
                    )
                    time.sleep(10)
                    continue
                else:
                    print(text)
                    return
            else:
                print(
                    f"Failed to get the query result. Status Code: {result_response.status_code}",
                    file=sys.stderr,
                )
                return None
    else:
        print(f"Failed to request the query. Status Code: {response.status_code}", file=sys.stderr)
        return None


if __name__ == "__main__":
    flexquery_download()
