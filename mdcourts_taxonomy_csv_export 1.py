import csv
import os
from sys import setrecursionlimit

# skip_dirs = {"css", "docs", "documents", "img", "images", "inc", "pdfs", "js"}


def getAllFolderNames(currentFolderPath, allFoldersList):
    """
    Recursively collect all folder names starting from the current folder path
    and add them to the allFoldersList.

    Parameters:
    - currentFolderPath: str, the path to the current folder to inspect
    - allFoldersList: list, a list where collected folder names will be added
    """
    # Ensure the current folder path is absolute
    currentFolderPath = os.path.abspath(currentFolderPath)

    isHtmlPresent = False
    # Iterate over the items in the current folder
    for item in os.listdir(currentFolderPath):
        # Construct the full path to the item
        # if item.lower() in skip_dirs:
        #     continue
        itemFullPath = os.path.join(currentFolderPath, item)
        # Check if the item is a directory
        if os.path.isdir(itemFullPath):
            # Recursively call this function on the subdirectory
            isHtmlPresentInSubfolder = getAllFolderNames(itemFullPath, allFoldersList)
            if isHtmlPresentInSubfolder:
                allFoldersList.append(itemFullPath)
                isHtmlPresent = True
        elif os.path.isfile(itemFullPath) and (itemFullPath.endswith('.html') or itemFullPath.endswith('.htm')):
            # If it is an HTML file, set isHtmlPresent = True
            isHtmlPresent = True
    return isHtmlPresent


def getAllFoldersDict(allFoldersDict, allFoldersList):
    termidcounter = 0
    for folderpath in reversed(allFoldersList):
        termidcounter += 1
        parent_path = os.path.dirname(folderpath)
        parent_id = allFoldersDict[parent_path][0] if parent_path in allFoldersDict else ''
        allFoldersDict[folderpath] = (termidcounter, parent_id)


def writeToCsv(allFoldersDict: dict, csvpath):
    with open(csvpath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['path', 'name', 'term_description', 'parent_term_desc'])  # CSV Header
        for folderpath in allFoldersDict.keys():
            folder_name = os.path.basename(folderpath)
            termid = allFoldersDict[folderpath][0]
            parenttermid = allFoldersDict[folderpath][1]
            writer.writerow([folderpath, folder_name, termid, parenttermid])

# Example usage
allFoldersList1 = []
allFoldersDict1 = {}
# rootfolderpath = "D:\\Fantail\\Projects\\New Search"
# csvfilepath = "D:\\Fantail\\Projects\\MdCourts\\Test\\localtest.csv"
rootfolderpath = "/home/ubuntu/courtnet_files/courtnet"
csvfilepath = "/home/ubuntu/csvs/taxonomyterms_htmlfolders.csv"
setrecursionlimit(10000)
getAllFolderNames(rootfolderpath, allFoldersList1)
getAllFoldersDict(allFoldersDict1, allFoldersList1)
writeToCsv(allFoldersDict1, csvfilepath)
