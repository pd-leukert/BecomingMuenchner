from google.cloud import storage

BUCKET_NAME = "data-pdf-2025"

def get_pdf_urls():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    blobs = bucket.list_blobs()

    urls = []

    for blob in blobs:
        url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}"
        urls.append(url)

    return urls

def upload_pdf(file_path, destination_blob_name):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    url = f"https://storage.googleapis.com/{BUCKET_NAME}/{destination_blob_name}"
    return url

def delete_pdf(blob_name):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)

    blob.delete()
    return True

