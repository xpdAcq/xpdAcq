$PROJECT = 'xpdAcq'
$ACTIVITIES = [
    'version_bump',
    'changelog',
    'tag',
    'push_tag',
#    'ghrelease',
    'pypi',
    'forge'
]

$VERSION_BUMP_PATTERNS = [
    ('xpdacq/__init__.py', '__version__\s*=.*', "__version__ = '$VERSION'"),
    ('setup.py', 'version\s*=.*,', "version='$VERSION',")
]
$CHANGELOG_FILENAME = 'CHANGELOG.rst'
$CHANGELOG_IGNORE = ['TEMPLATE.rst']
$PUSH_TAG_REMOTE ='https://github.com/xpdAcq/xpdAcq.git'

$GITHUB_REPO = 'xpdAcq'
$GITHUB_ORG = 'xpdAcq'

$LICENSE_URL = 'https://github.com/{}/{}/blob/master/LICENSE'.format($GITHUB_ORG, $GITHUB_REPO)

from urllib.request import urlopen
rns = urlopen('https://raw.githubusercontent.com/xpdAcq/mission-control/master/tools/release_not_stub.md').read().decode('utf-8')
$GHRELEASE_PREPEND = rns.format($LICENSE_URL, $PROJECT.lower())

$FORGE_FEEDSTOCK = 'git@github.com:nsls-ii-forge/xpdacq-feedstock.git'
$FORGE_FEEDSTOCK_ORG = 'nsls-ii-forge'
$FORGE_PROTOCOL = 'ssh'
$FORGE_SOURCE_URL = 'https://github.com/$GITHUB_ORG/$GITHUB_REPO/releases/download/$VERSION/$PROJECT-$VERSION.tar.gz'
$FORGE_HASH_TYPE = 'sha256'
$FORGE_PULL_REQUEST = True
$FORGE_RERENDER = True
$FORGE_USE_GIT_URL = False
