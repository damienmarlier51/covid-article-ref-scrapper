Much of the codebase is from https://github.com/ismms-himc/covid-19_sinai_reviews.</br>
Code was editer to cater for use case described below.

# Objective

Goal is to make it easier for researchers to identify and review relevant COVID articles.

The idea is as followed:
Researchers use google spreadsheet as a collaborative tool.
- They will use one tab (*Tab1*) for listing articles which have already been listing by a group member.
- Another tab (*Tab2*) is used as a pool for all other COVID-related articles not yet reviewed.

The objective of this code is to periodically retrieve any COVID related articles from Biorxiv (https://www.biorxiv.org/) and paste their references into Tab2 so that researchers keep-up with new published articles.

To avoid redundancy between *Tab1* and *Tab2*, articles whose DOI (Digital Object Identifier) are already in *Tab1* are not pasted into *Tab2*.

Article references are also enriched using a relavance score which is computed using http://api.altmetric.com.

# Deployment

Changes were made such as the code can be deployed on GCP Cloud Function. </br>
It can also be easily scheduled via Cloud Scheduler.

In current use case, script is scheduled to run twice a day.

- Update constant variables in main.py
- Get Gsheet credentials from https://console.developers.google.com/apis/
- Update variables in ```src/main.py```
- Run once main.py with ```use_cloud_function=False```
- Deploy to GCP Cloud Function
  ```bash deploy.sh```

# Example

https://docs.google.com/spreadsheets/d/1YPLXlf5vNs6oGJUno0H3Kn_XD1VT67M9s8sc239cetY/edit?usp=sharing

- Sheet1 contains articles currently reviewed
- Sheet2 contains articled yet to be reviewed
Articles in Sheet1 are not in Sheet2 and vice-versa.

Feel free to improve on this repo!
