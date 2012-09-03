import logging
import os
from shutil import copyfileobj
from tempfile import NamedTemporaryFile

import urllib2
from django.core.files import File
from celery.task import task

import xmlrpclib

from localshop.apps.packages import models

from localshop.utils import now
from localshop.apps.packages import forms
from localshop.apps.packages import models

logger = logging.getLogger(__name__)

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


@task
def update_packages():
    logging.info('Updated packages')
    for package in models.Package.objects.filter(is_local=False):
        logging.info('Updating package %s', package.name)
        get_package_data.delay(package.name, package)
    logging.info('Complete')


class Urllib2Transport(xmlrpclib.Transport):
    def __init__(self, opener=None, https=False, use_datetime=0):
        xmlrpclib.Transport.__init__(self, use_datetime)
        self.https = https
    
    def request(self, host, handler, request_body, verbose=0):
        proto = ('http', 'https')[bool(self.https)]
        req = urllib2.Request('%s://%s%s' % (proto, host, handler), request_body)
        req.add_header('User-agent', self.user_agent)
        req.add_header("Content-Type", "text/xml")
        self.verbose = verbose
        return self.parse_response(urllib2.urlopen(req))

@task
def get_package_data(name, package=None):
    """Retrieve metadata information for the given package name"""
    if not package:
        package = models.Package(name=name)
        releases = {}
    else:
        releases = package.get_all_releases()

    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=Urllib2Transport())

    versions = client.package_releases(package.name, True)

    # package_releases() method is case-sensitive, if nothing found
    # then we search for it
    # XXX: Ask pypi to make it case-insensitive?
    if not versions:
        for item in client.search({'name': name}):
            if name.lower() == item['name'].lower():
                package.name = name = item['name']
                break
        else:
            logger.info("No packages found matching %r", name)
            return

        # Retry retrieving the versions with the new/correct name
        versions = client.package_releases(package.name, True)

    # Save the package if it is new
    if not package.pk:
        package.save()

    for version in versions:
        release, files = releases.get(version, (None, {}))
        if not release:
            release = models.Release(package=package, version=version)
            release.save()

        data = client.release_data(package.name, release.version)

        release_form = forms.PypiReleaseDataForm(data, instance=release)
        if release_form.is_valid():
            release_form.save()

        release_files = client.package_urls(package.name, release.version)
        for info in release_files:
            release_file = files.get(info['filename'])
            if not release_file:
                release_file = models.ReleaseFile(
                    release=release, filename=info['filename'])

            release_file.python_version = info['python_version']
            release_file.filetype = info['packagetype']
            release_file.url = info['url']
            release_file.size = info['size']
            release_file.md5_digest = info['md5_digest']
            release_file.save()

    package.update_timestamp = now()
    package.save()
