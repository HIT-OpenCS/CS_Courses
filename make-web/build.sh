python update.py
mkdocs build --clean
rm -rf ../docs
cp -r site ../docs
echo -e "\nThe website update is complete. Please check the website locally and press Ctrl+C to exit.\n"
mkdocs serve