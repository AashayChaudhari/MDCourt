from bs4 import BeautifulSoup, Comment
import csv
import os
import unicodedata
import re 


# Define the base URL and directory path for the files.
# base_url = "https://drupal.courtnet.fantailtech.com/sites/default/files"
base_url = "/sites/default/files"
directory_path = '/home/ubuntu/courtnetall/courtnet'
delimiter = "|"

error_files = []

def read_navigation_links(inc_folder_path):
    nav_file_path = os.path.join(inc_folder_path, 'leftnavigation.html').replace("\\","/").replace("\\\\", "/").replace("//", "/")
    links = set()
    try:
        with open(nav_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            for a in soup.find_all('a', href=True):
                # Assume the href attribute of anchor tags would be a relative path to html files
                # Extract the href and append to base directory to get the full relative path
                href = os.path.join(inc_folder_path.replace(directory_path, '').lstrip('/'), a['href'])
                href = os.path.normpath(href).replace('\\', '/')
                links.add(href)
    except FileNotFoundError:
        print(f'No leftnavigation.html file found in {inc_folder_path}')
    return links

def detect_encoding(html_path):
    """Detects encoding specified in the HTML meta tag."""
    try:
        with open(html_path, 'rb') as file:
            content_head = file.read(1024).decode('ascii', errors='ignore')  # Read first 1024 bytes as ASCII
            match = re.search(r'charset=["\']?([\w-]+)', content_head, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'iso-8859-1'  # Default to iso-8859-1 if no charset found
    except UnicodeDecodeError:
        return 'iso-8859-1'  # Fallback to a different encoding if utf-8 fails

def extract_html_content(html_path, relative_path, error_log):
    """Extracts and processes HTML content with dynamic encoding detection."""
    try:
        encoding = detect_encoding(html_path)
        with open(html_path, 'r', encoding=encoding) as file:
                soup = BeautifulSoup(file, 'html.parser')

                for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                    if 'include virtual=' in comment:
                        if 'navigation.html' not in comment \
                            and 'leftnavigation.html' not in comment \
                            and 'footer.html' not in comment \
                            and 'topie.html' not in comment \
                            and 'head.html' not in comment \
                            and 'innerpagescript.html' not in comment:
                            # Parse the SSI tag to extract the virtual path
                            include_virtual = comment.strip().split('=')[1].strip('"\'')
                            include_virtual_path = os.path.join(relative_path, include_virtual).replace("\\","/").replace("\\\\", "/").replace("//", "/")
                            include_virtual_path = os.path.normpath(include_virtual_path).replace('\\', '/').replace("//", "/")
                            # include_virtual_path = os.path.join(directory_path, include_virtual_path)
                            include_virtual_path = directory_path + "/"+ include_virtual_path

                            include_virtual_path = include_virtual_path.replace('\\', '/').replace("\\\\", "/").replace("//", "/")

                            # Read the content of the included virtual file
                            try:
                                with open(include_virtual_path, 'r', encoding='iso-8859-1') as inc_file:
                                    inc_soup = BeautifulSoup(inc_file, 'html.parser')
                                    # Find the body content of the included file
                                    inc_body = inc_soup.body
                                    # Replace the SSI tag with the content of the included file
                                    if inc_body:
                                    # Replace the SSI tag with the content of the included file
                                        comment.replace_with(inc_body)
                                    else:
                                        comment.replace_with(inc_soup)
                            except FileNotFoundError:
                                print(f'Included file not found: {include_virtual_path}')        

                #Remove comments
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment.extract()


                for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                    #Remove SSI tags
                    if 'include virtual':
                        comment.extract()

                # Update img src attributes
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src and not src.startswith(('http:', 'https:')):
                        full_path = os.path.join(relative_path, src).replace("\\","/").replace("\\\\", "/").replace("//", "/")
                        full_path = os.path.normpath(full_path).replace('\\', '/').replace("\\\\", "/").replace("//", "/")
                        full_url = base_url + '/' + full_path
                        img['src'] = full_url

                # Update anchor href attributes for PDF files
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.endswith('.pdf') and not href.startswith(('http:', 'https:')):
                        full_path = os.path.join(relative_path, href).replace("\\","/").replace("\\\\", "/").replace("//", "/")
                        full_path = os.path.normpath(full_path).replace('\\', '/').replace("\\\\", "/").replace("//", "/")
                        full_url = base_url + '/' + full_path
                        a['href'] = full_url

                # Extract the first h1 tag content for the title
                title_tag = soup.find('h1')
                if not title_tag:
                    # If no h1 tag, try to find the title tag
                    title_tag = soup.find('title')

                # If a title tag or h1 tag is found, get the combined text, otherwise use a blank space
                # title_html = title_tag.get_text(strip=True).replace('"', "'").replace('\n', ' ').replace('\r', ' ') if title_tag else ' '
                title_html = (title_tag.get_text(strip=True).replace('"', "'").replace('\n', ' ').replace('\r', ' ')
                            if title_tag and title_tag.get_text(strip=True) != '' else ' ')

                print("title_html is : ", title_html)

                # Remove the first h1 tag from the body
                if soup.body and soup.body.find('h1'):
                    soup.body.find('h1').extract()

                # Extract and modify the HTML of the body tag
                body_html = ''.join([str(tag) for tag in soup.body.contents]) if soup.body else ' '
                body_html = body_html.replace('"', "'").replace('\n', '').replace('\r', '').replace('--&gt', '')


                # Replace curly quotes and other typographical marks directly
                replacements = {
                    "‘": "'", "’": "'",  # Single quotes
                    "“": '"', "”": '"',  # Double quotes
                    "–": "-", "—": "-",  # En dash and em dash
                    "…": "..."           # Ellipsis
                }

                for search, replace in replacements.items():
                    title_html = title_html.replace(search, replace)
                    body_html = body_html.replace(search, replace)

                title_html = title_html.replace('|', ':')
                body_html = body_html.replace('|', ':')

                return title_html, body_html
    except UnicodeDecodeError:
        error_log.append(html_path)  # Log the file path where the error occurred
        return 'Encoding error', None  # Return a placeholder or error message


def readFromCsv(allFoldersDict: dict, csvpath):
    with open(csvpath, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            folderpath, folder_name, termid, parenttermid = row
            allFoldersDict[folderpath] = [termid, parenttermid]
    return allFoldersDict

# Define CSV file path
csv_file_path = '/home/ubuntu/new_csvs/articles_export.csv'
termid_csv_file_path = '/home/ubuntu/new_csvs/taxonomy_terms_htmlfolders.csv'
folderpathDict = {}
readFromCsv(folderpathDict, termid_csv_file_path)

# Create CSV file and write headers
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=delimiter)
    csv_writer.writerow(
        ['title', 'body', 'dir', 'old_url', 'display_nav_bar'])

print("Checking for directories and files")
# Search for 'index.html' in the given directory and subdirectories.
for root, dirs, files in os.walk(directory_path, topdown=True):
    # Exclude 'inc' directory from the list of directories to avoid adding its contents to the CSV
    dirs[:] = [d for d in dirs if d != 'inc']
    nav_links = set()

    # Check if there's an 'inc' folder within the current directory and read its navigation links
    if 'inc' in os.listdir(root):
        inc_folder_path = os.path.join(root, 'inc').replace("\\","/").replace("\\\\", "/").replace("//", "/")
        nav_links = read_navigation_links(inc_folder_path)

    # buffer_root = "/home/ubuntu/courtnet_files/courtnet" + root[len(directory_path):].replace("\\", "/")
    # print("buffer root: ", buffer_root)
    buffer_root = root

    directory_termid = folderpathDict[buffer_root][0] if buffer_root in folderpathDict else ''


    for file_name in files:
        if file_name.endswith('.html') or file_name.endswith('.htm'):
            file_path = os.path.join(root, file_name).replace("\\","/").replace("\\\\", "/").replace("//", "/")
            immediate_dir = os.path.basename(os.path.dirname(file_path))
            relative_path = os.path.relpath(root, directory_path)
            relative_path = relative_path.replace('\\', '/')  # Ensure URL compatibility
            title, body = extract_html_content(file_path, relative_path, error_files)

            clean_title = title.replace('"', '')
            # Calculate the full URL to the HTML file
            old_url = '/' + os.path.join(relative_path, file_name).replace('\\', '/').replace("\\\\", "/").replace("//", "/")
            # Determine if the current file is in the navigation bar

            if old_url in nav_links:
                display_nav_bar = True
            else:
                display_nav_bar = ""

            # Write to CSV, but skip files in 'inc' directory
            if immediate_dir != 'inc':
                with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=delimiter)
                    csv_writer.writerow([clean_title, body, directory_termid, old_url, display_nav_bar])


# Optionally, write the error log to a file
if error_files:
    with open('error_log.txt', 'w') as f:
        for filename in error_files:
            f.write(f"{filename}\n")


# Confirm the creation of the CSV file
if os.path.isfile(csv_file_path):
    print("CSV file created:", csv_file_path)
else:
    print("No 'index.html' file found in the directory.")
