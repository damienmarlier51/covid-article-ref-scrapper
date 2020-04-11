from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import storage

import os
import pandas as pd
import requests
import json

BASE_URL = 'http://api.altmetric.com/v1/doi/'
BIORXIV_ENDPOINT = 'https://connect.biorxiv.org/relate/collection_json.php?grp=181'

#  GSHEET
CREDENTIAL_PATH = "<YOUR GSHEET API CREDENTIALS>.json"  # e.g "../gsheets_credentials.json"
GSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Token for accessing gsheet api, refreshed at every run
TOKEN_FILENAME = "token.pickle"
TOKEN_FILEPATH = TOKEN_FILENAME

SHEET_ID = "<YOUR GSHEET ID>"  # e.g ("1b2LYi9iRrTHuKckumU3fmxnL6NWwf9aSJGw8xUoSlA")
DOI_SHEET = "Sheet1"
DEST_SHEET = "Sheet2"
DOI_COLUMN = "ID (DOI/PMID/etc) with link"

CSV_FILENAME = "update_paper_reviews.csv"
CSV_FILEPATH = CSV_FILENAME

use_cloud_function = True
if use_cloud_function is True:
    TOKEN_FILEPATH = "/tmp/{}".format(TOKEN_FILENAME)
    CSV_FILEPATH = "/tmp/{}".format(CSV_FILENAME)

# BUCKET WHERE TO STORE GSHEET ACCESS TOKEN
BUCKET_NAME = "update_paper_reviews"


def get_gsheet_service(storage_client):

    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(TOKEN_FILENAME)

    try:
        blob.download_to_filename(TOKEN_FILEPATH)
    except Exception as e:
        print(str(e))
        if use_cloud_function is True:
            raise Exception("Missing token in bucket")

    creds = None
    if os.path.exists(TOKEN_FILEPATH) is True:
        with open(TOKEN_FILEPATH, 'rb') as token:
            try:
                creds = pickle.load(token)
            except Exception:
                creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIAL_PATH, GSHEET_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILEPATH, 'wb') as token:
            pickle.dump(creds, token)

    blob.upload_from_filename(TOKEN_FILEPATH)

    service = build('sheets', 'v4', credentials=creds)

    return service


def download_collection():

    r = requests.get(BIORXIV_ENDPOINT)
    collection = r.text
    req_dict = json.loads(collection)

    return req_dict


def get_scores(req_dict):

    arr_papers = req_dict['rels']
    print('Number of papers', len(arr_papers))

    inst_papers = []
    for i, inst_paper in enumerate(arr_papers):

        inst_doi = inst_paper['rel_doi']
        inst_paper['score'] = None
        inst_paper['details_url'] = None

        r = requests.get(BASE_URL + inst_doi)
        if r.text != 'Not Found':
            alt_req_dict = json.loads(r.text)
            inst_paper['score'] = alt_req_dict['score']
            inst_paper['details_url'] = alt_req_dict['details_url']

        inst_papers.append(inst_paper)

        if i % 50 == 0:
            print('Scored {} papers'.format(i + 1))

    df_papers = pd.DataFrame.from_dict(inst_papers, orient='columns')

    return df_papers


def main(data, context):

    # Instantiates a client
    storage_client = storage.Client()

    # Call the Sheets API
    service = get_gsheet_service(storage_client=storage_client)

    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=SHEET_ID,
                                range=DOI_SHEET,).execute()
    values = result.get('values', [])

    df = pd.DataFrame(data=values[1:],
                      columns=values[0])

    DOIs = df[DOI_COLUMN].values.tolist()

    print("Start download collection...")
    req_dict = download_collection()

    print("Get scores...")
    df_papers = get_scores(req_dict)
    df_papers = df_papers[~df_papers.isin(DOIs)]
    df_papers.sort_values(by=["score"], ascending=False)
    df_papers.fillna(value="NaN", inplace=True)
    df_papers.to_csv(CSV_FILEPATH, index=None)

    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(CSV_FILENAME)
    blob.upload_from_filename(CSV_FILEPATH)

    papers_list = df_papers.values.tolist()
    body = {"values": papers_list}

    print("Clear...")
    result = sheet.values().clear(spreadsheetId=SHEET_ID,
                                  range=DEST_SHEET).execute()

    print("Update...")
    result = sheet.values().update(spreadsheetId=SHEET_ID,
                                   range=DEST_SHEET,
                                   valueInputOption="RAW",
                                   body=body).execute()


if __name__ == "__main__":
    main(data={}, context=None)
