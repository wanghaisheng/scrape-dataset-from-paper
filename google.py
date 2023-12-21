if I got a keyword, I want you to search against arxiv.org to find all the reavlant paper, download each pdf then analyse the contents, use google gemini to detect whether there is a public available dataset name and possible download link
python
﻿ ```python
import requests
from bs4 import BeautifulSoup
import os
import re
from google.cloud import storage
from google.cloud import gemini

def search_arxiv(keyword):
  """
  Search arxiv.org for papers containing the given keyword.

  Args:
    keyword: The keyword to search for.

  Returns:
    A list of tuples containing the title and URL of each relevant paper.
  """

  # Construct the search URL.
  search_url = f"https://arxiv.org/search/?query={keyword}&searchtype=all&abstracts=show"

  # Send a GET request to the search URL.
  response = requests.get(search_url)

  # Parse the HTML response.
  soup = BeautifulSoup(response.text, "html.parser")

  # Find all the paper titles and URLs.
  paper_titles = [h3.get_text() for h3 in soup.find_all("h3", class_="title mathjax")]
  paper_urls = [a["href"] for a in soup.find_all("a", class_="abs") if "pdf" in a["href"]]

  # Return a list of tuples containing the title and URL of each relevant paper.
  return list(zip(paper_titles, paper_urls))


def download_paper(url):
  """
  Download the PDF of a paper from the given URL.

  Args:
    url: The URL of the paper to download.

  Returns:
    The local path to the downloaded PDF file.
  """

  # Get the filename from the URL.
  filename = url.split("/")[-1]

  # Send a GET request to the paper URL.
  response = requests.get(url, stream=True)

  # Save the PDF file to the local filesystem.
  with open(filename, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024):
      if chunk:
        f.write(chunk)

  return filename


def analyze_paper(filename):
  """
  Analyze the contents of a paper.

  Args:
    filename: The local path to the paper to analyze.

  Returns:
    A dictionary containing the title, authors, abstract, and keywords of the paper.
  """

  # Load the PDF file.
  with open(filename, "rb") as f:
    pdf_bytes = f.read()

  # Extract the title, authors, abstract, and keywords from the PDF file.
  title = re.search(r"^Title: (.*)$", pdf_bytes.decode("utf-8"), re.MULTILINE).group(1)
  authors = re.search(r"^Authors: (.*)$", pdf_bytes.decode("utf-8"), re.MULTILINE).group(1)
  abstract = re.search(r"^Abstract: (.*)$", pdf_bytes.decode("utf-8"), re.MULTILINE).group(1)
  keywords = re.findall(r"^Keywords: (.*)$", pdf_bytes.decode("utf-8"), re.MULTILINE)

  # Return a dictionary containing the title, authors, abstract, and keywords of the paper.
  return {
      "title": title,
      "authors": authors,
      "abstract": abstract,
      "keywords": keywords
  }


def detect_dataset(filename):
  """
  Detect the presence of a public dataset in a paper.

  Args:
    filename: The local path to the paper to analyze.

  Returns:
    A tuple containing the name of the dataset and a link to download it, if available.
  """

  # Load the PDF file.
  with open(filename, "rb") as f:
    pdf_bytes = f.read()

  # Initialize the Google Cloud Storage client.
  storage_client = storage.Client()

  # Initialize the Google Cloud Gemini client.
  gemini_client = gemini.Client()

  # Search for public datasets in the paper.
  for match in re.finditer(r"https://storage.googleapis.com/(.*?)/", pdf_bytes.decode("utf-8")):
    # Get the bucket name and blob name from the match.
    bucket_name, blob_name = match.group(1).split("/")

    # Check if the bucket exists.
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
      continue

    # Check if the blob exists.
    blob = bucket.blob(blob_name)
    if not blob.exists():
      continue

    # Check if the blob is public.
    if not blob.acl.public_read:
      continue

    # Get the dataset name.
    dataset_name = blob_name.split("/")[-1]

    # Get the dataset download link.
    download_link = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    # Return the dataset name and download link.
    return dataset_name, download_link

  # No public dataset found.
  return None, None


if __name__ == "__main__":
  # Get the keyword from the user.
  keyword = input("Enter a keyword: ")

  # Search arxiv.org for papers containing the given keyword.
  papers = search_arxiv(keyword)

  # Download each paper.
  for title, url in papers:
    filename = download_paper(url)

    # Analyze the contents of the paper.
    paper_info = analyze_paper(filename)

    # Detect the presence of a public dataset in the paper.
    dataset_name, download_link = detect_dataset(filename)

    # Print the paper information.
    print(f"Title: {paper_info['title']}")
    print(f"Authors: {paper_info['authors']}")
    print(f"Abstract: {paper_info['abstract']}")
    print(f"Keywords: {paper_info['keywords']}")

    # Print the dataset information, if available.
    if dataset_name is not None and download_link is not None:
      print(f"Dataset Name: {dataset_name}")
      print(f"Dataset Download Link: {download_link}")
