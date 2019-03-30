# icd10data-scraper

Load ICD codes and find appopriate synonyms for a code
data can be found at: http://icd10data.com/

## Requirements:
This web app scrapes icd10data and lazily stores codes and appropriate synonyms in a local mongo db

You must run:
```
 $ pip3 install -r requirements.txt
```

## Usage:

### Code->synonyms mapping
Run the app:
```
 $ python3 run.py
```

Get a code's synonyms:
```
 $ curl http://localhost:8080/code/<code>
```

Given a list of codes in codes.txt:
```
 $ for i in `cat codes.txt`; do curl http://localhost:8080/code/$i ; done
```

### Scrapper
Load codes into a database - optional, but will prepopulate all codes (the speed here can be improved):
Start Mongo db locally (Mac)

```
brew install mongodb
brew tap homebrew/services
brew services start mongodb
```

```
 $ python3 scraper.py
```

Export data from Mongo to a JSON file
```bash
mongoexport --host localhost --db icdcodes --collection ICDCode --type=json --out ~/Downloads/icdcodes.json
```

Backup
```bash
mongodump --collection ICDCode --db icdcodes --out ~/Downloads/mongo_backup/
```