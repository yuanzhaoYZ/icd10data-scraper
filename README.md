# icd10data-scraper

Load ICD codes and find appopriate synonyms for a code
data can be found at: http://icd10data.com/

## Requirements:
This web app scrapes icd10data and lazily stores codes and appropriate synonyms in a local mongo db

You must run:
```
 conda create -n icd_scraper python=3.6
 source activate icd_scraper
 pip install -r requirements.txt
```

## Usage:

### Code->synonyms mapping
Run the app:
```
source activate icd_scraper
python run.py
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
source activate icd_scraper
python scraper.py
```

Export data from Mongo to a JSON file
```bash
mongoexport --host localhost --db icdcodes --collection ICDCode --type=json --out ~/Downloads/icdcodes.json
```

Backup
```bash
mongodump --collection ICDCode --db icdcodes --out ~/Downloads/mongo_backup/
```
### data_scraper.py
Load ICD codes and find fields like code, name, subclass, synonyms, applicableTo, ClinicalInfos, DRGCodes, etc
This program will scrapes icd10data and stores fields in a local file
```bash
python data_scraper.py
```
### drg_codes_scraper.py
Load DRG codes and find fields like code, name, Related Groups List codes
data can be found at : https://www.icd10data.com/ICD10CM/DRG
This program will scrapes DRG data and stores fileds in a local file
