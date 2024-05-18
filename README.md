# EEA Coding tests

This is a minimal FastAPI app that you will modify for the EEA coding assignment.
Although it does run with with the instructions provided below, it has a number of bugs and problems
Your coding exercise is to fix it, dockerize it, and add one small feature

The models are very generic; there are Users and Items.
An Item has an owner which is a User.
And there is an ItemHistory table which tracks changes to owners.

For this exercise:
1. Find and fix the bugs and reliability issues
2. Add the following feature:
	in the Item model, there is a status field that is currently unused.
	Status can be one of ('NEW', 'APPROVED', 'EOL')
	Allow an API to change an Items status
	Allow an API to list all Items having a particular status
	Track the history of these changes in the DB
	(These requirements might seem a bit vague; use your judgement on how best to implement this with the information you have, but if you have any questions you may ask them)
4. Create a dockerfile and docker-compose file so that this project can be run with docker-compose
5. Make any other changes to the project that you think would be necessary to run this in production.
  You may not have time to actually do everything that you would like; please add any suggestions that you did not have time to implement to this README
	
### Install the requrements
`pip install -r requirements.txt`

### Set up the DB
You will need a mysql db running locally on port 3306
with user testuser:pass and database items
(or you can change the connection string)

If the DB is accessible, tables will be automatically created when the app starts

### Start the application
`uvicorn main:app --reload`

### auto generated docs
http://127.0.0.1:8000/docs
