$PROJECT = 'xpdAcq'
$ACTIVITIES = ['version_bump',
               'changelog',
               'tag',
               'push_tag',
               'ghrelease']

$VERSION_BUMP_PATTERNS = [
    ('xpdacq/__init__.py', '__version__\s*=.*,', "__version__ = '$VERSION',"),
    ('setup.py', 'version\s*=.*,', "version='$VERSION',")
    ]
$CHANGELOG_FILENAME = 'CHANGELOG.rst'
$CHANGELOG_IGNORE = ['TEMPLATE.rst']
$TAG_REMOTE = 'git@github.com:xpdAcq/xpdAcq.git'

$GITHUB_REPO = 'xpdAcq'
$GITHUB_ORG = 'xpdAcq'
$LICENSE_URL = 'https://github.com/{}/{}/blob/master/LICENSE'.format($GITHUB_ORG, $GITHUB_REPO)
$GHRELEASE_PREPEND = open('release_note_stub.rst', 'r').read().format($LICENSE_URL, $PROJECT.lower())
