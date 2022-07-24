# RP Tagger
Web-based UI made for managing image folders using a tagging system.

# Requirements
To install all requirements, use the following snippet after installing python on your machine.

    pip install -r requirements/pro.txt

# Usage

Add the module to the PYTHONPATH

    export PYTHONPATH=$PWD/src
    
Create the database.

    ./rp_tagger migrate

Run the server

    ./rp_tagger runserver

It will load all images from the Downloads folder by default
