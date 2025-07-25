@echo off
echo Adding all changes to Git...
git add .

set /p commit_message="Enter commit message: "

echo Committing changes...
git commit -m "%commit_message%"

echo Pushing to Heroku...
git push heroku master

echo Deployment process finished.
pause