PROJECT_ID=scenic-scholar-247909; # Edit with your project name
FUNCTION_NAME=UpdatePaperReviews # Edit with your function name
gcloud functions deploy $FUNCTION_NAME \
--entry-point main \
--source src \
--runtime python37 \
--timeout 540s \
--project $PROJECT_ID \
--trigger-topic $FUNCTION_NAME \
--memory 1GB
