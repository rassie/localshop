import logging
import os
from shutil import copyfileobj
from tempfile import NamedTemporaryFile

import urllib2
from django.core.files import File
from celery.task import task

from localshop.apps.packages import models

@task
def download_file(pk):
    release_file = models.ReleaseFile.objects.get(pk=pk)
    logging.info("Downloading %s", release_file.url)
    response = urllib2.urlopen(release_file.url)

    # Store the content in a temporary file
    tmp_file = NamedTemporaryFile()
    copyfileobj(response, tmp_file)

    # Write the file to the django file field
    filename = os.path.basename(release_file.url)
    release_file.distribution.save(filename, File(tmp_file))
    release_file.save()
    logging.info("Complete")
