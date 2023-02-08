# Assumes there's a script called "isolate_suffolk.sh" that is the 

python3 docassemble.ALLinter.bulk_download
find . -maxdepth 1 -type d | xargs -I % sh -c 'cd % && ../isolate_suffolk.sh `git remote get-url origin` %'
cd ../../all_suffolk_data
find . -wholename */templates/*.pdf | xargs -I % cp % .

