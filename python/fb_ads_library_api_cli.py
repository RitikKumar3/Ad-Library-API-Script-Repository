#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import sys

from fb_ads_library_api import FbAdsLibraryTraversal
from fb_ads_library_api_operators import get_operators, save_to_csv
from fb_ads_library_api_utils import get_country_code, is_valid_fields


def get_parser():
    parser = argparse.ArgumentParser(
        description="The Facebook Ads Library API CLI Utility"
    )
    parser.add_argument(
        "-t",
        "--access-token",
        help="The Facebook developer access token",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--fields",
        help="Fields to retrieve from the Ad Library API",
        required=True,
        type=validate_fields_param,
    )
    parser.add_argument("-s", "--search-terms", help="Multiple search terms separated by commas")
    parser.add_argument(
        "-c",
        "--country",
        help="Comma-separated country code (no spaces)",
        required=True,
        type=validate_country_param,
    )
    parser.add_argument(
        "--search-page-ids", help="The specific Facebook Page you want to search"
    )
    parser.add_argument(
        "--ad-active-status",
        help="Filter by the current status of the ads at the moment the script runs",
    )
    parser.add_argument(
        "--after-date", help="Only return ads that started delivery after this date"
    )
    parser.add_argument("--batch-size", type=int, help="Batch size")
    parser.add_argument(
        "--retry-limit",
        type=int,
        help="When an error occurs, the script will abort if it fails to get the same batch this amount of times",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    actions = ",".join(get_operators().keys())
    parser.add_argument(
        "action", help="Action to take on the ads, possible values: %s" % actions
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="The parameter for the specific action"
    )
    return parser


def validate_country_param(country_input):
    if not country_input:
        return ""
    country_list = list(filter(lambda x: x.strip(), country_input.split(",")))
    if not country_list:
        raise argparse.ArgumentTypeError("Country cannot be empty")
    valid_country_codes = list(map(lambda x: get_country_code(x), country_list))
    invalid_inputs = {
        key: value
        for (key, value) in zip(country_list, valid_country_codes)
        if value is None
    }

    if invalid_inputs:
        raise argparse.ArgumentTypeError(
            "Invalid/unsupported country code: %s" % (",".join(invalid_inputs.keys()))
        )
    else:
        return ",".join(valid_country_codes)


def validate_fields_param(fields_input):
    if not fields_input:
        return False
    fields_list = list(
        filter(lambda x: x, map(lambda x: x.strip(), fields_input.split(",")))
    )
    if not fields_list:
        raise argparse.ArgumentTypeError("Fields cannot be empty")
    invalid_fields = list(filter(lambda x: not is_valid_fields(x), fields_list))
    if not invalid_fields:
        return ",".join(fields_list)
    else:
        raise argparse.ArgumentTypeError(
            "Unsupported fields: %s" % (",".join(invalid_fields))
        )


def main():
    parser = get_parser()
    opts = parser.parse_args()

    if not opts.search_term and not opts.search_page_ids:
        print("At least one must be set: --search-term, --search-page-ids")
        sys.exit(1)

    search_terms = opts.search_terms.split(",") if opts.search_terms else [""]  # Split the search terms by commas
    fields = "search_term," + opts.fields
    all_results = []

    for search_term in search_terms:
        search_term = search_term.strip()
        api = FbAdsLibraryTraversal(
            opts.access_token, fields, search_term, opts.country
        )
        if opts.search_page_ids:
            api.search_page_ids = opts.search_page_ids
        if opts.ad_active_status:
            api.ad_active_status = opts.ad_active_status
        if opts.batch_size:
            api.page_limit = opts.batch_size
        if opts.retry_limit:
            api.retry_limit = opts.retry_limit
        if opts.after_date:
            api.after_date = opts.after_date
        generator_ad_archives = api.generate_ad_archives()

        for ad_archives in generator_ad_archives:
            for ad in ad_archives:
                ad['search_term'] = search_term  # Add the search term to the ad data
                all_results.append(ad)

    if opts.action in get_operators():
        if opts.action == "save_to_csv":
            save_to_csv(
                all_results, opts.args, fields, is_verbose=opts.verbose
            )
        else:
            get_operators()[opts.action](
                all_results, opts.args, is_verbose=opts.verbose
            )
    else:
        print("Invalid 'action' value: %s" % opts.action)
        sys.exit(1)


if __name__ == "__main__":
    main()

