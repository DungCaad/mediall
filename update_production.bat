@echo off
setlocal

cd /d "%~dp0"
set "DEPLOY_BRANCH=main"
set "DEPLOY_HOST=root@103.188.82.158"
set "DEPLOY_DIR=/mediall_en"

if "%~1"=="" (
    set "COMMIT_MESSAGE=Update Mediall production"
) else (
    set "COMMIT_MESSAGE=%~1"
)

echo [1/6] Checking Django...
python manage.py check --settings=mediall_en.test_settings || goto :failed

echo [2/6] Running tests...
python manage.py test --settings=mediall_en.test_settings || goto :failed

echo [3/6] Staging current project files...
git add -A || goto :failed
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "%COMMIT_MESSAGE%" || goto :failed
) else (
    echo No local changes to commit.
)

echo [4/6] Pushing %DEPLOY_BRANCH% to GitHub...
git push origin %DEPLOY_BRANCH% || goto :failed

echo [5/6] Updating production server...
ssh %DEPLOY_HOST% "cd %DEPLOY_DIR% && test -z \"$(git status --porcelain)\" && git pull --ff-only origin %DEPLOY_BRANCH% && sh scripts/deploy_after_pull.sh" || goto :failed

echo [6/6] Production update completed successfully.
exit /b 0

:failed
echo.
echo Update failed. Review the error above; production was not marked successful.
exit /b 1
