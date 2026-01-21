import random
from storage import storage

# A curated list of simple, memorable English words for short codes
WORD_LIST = [
    "apple", "banana", "cherry", "dragon", "eagle", "falcon", "garden", "harbor",
    "island", "jungle", "kitten", "lemon", "mango", "nectar", "orange", "panda",
    "quartz", "rabbit", "sunset", "tiger", "umbrella", "velvet", "walnut", "xenon",
    "yellow", "zebra", "amber", "breeze", "coral", "dawn", "ember", "frost",
    "glow", "honey", "ivory", "jade", "kite", "lotus", "marble", "nova",
    "opal", "pearl", "quest", "river", "storm", "thunder", "unity", "violet",
    "willow", "azure", "blaze", "cloud", "delta", "echo", "flame", "galaxy",
    "horizon", "indigo", "jewel", "karma", "lunar", "meadow", "noble", "ocean",
    "prism", "quill", "radiant", "silver", "twilight", "urban", "vivid", "wonder",
    "zephyr", "alpine", "bloom", "crystal", "drift", "eternal", "fern", "glacier",
    "haven", "iris", "jasper", "kindle", "lavender", "mystic", "nimbus", "orchid",
    "phantom", "quasar", "raven", "spark", "tempo", "utopia", "vortex", "whisper",
    "zenith", "aurora", "brass", "cinder", "dusk", "ember", "flare", "grace",
    "harmony", "icon", "jolt", "keeper", "legend", "mosaic", "nectar", "orbit",
    "pixel", "redux", "serenity", "terra", "unity", "vapor", "wander", "yarn"
]


def generate_short_id():
    """Generate a memorable short ID using dictionary words."""
    word = random.choice(WORD_LIST)
    suffix = random.randint(1, 99)
    short_id = f"{word}{suffix}"
    
    # Check if this ID already exists in storage
    while storage.file_exists(short_id):
        word = random.choice(WORD_LIST)
        suffix = random.randint(1, 99)
        short_id = f"{word}{suffix}"
    
    return short_id


def save_text_paste(content: str, filename: str) -> str:
    """Save text content to storage."""
    return storage.upload_text(filename, content)


async def save_upload_file(upload_file, filename: str) -> str:
    """Save an uploaded file to storage."""
    content = await upload_file.read()
    content_type = upload_file.content_type or "application/octet-stream"
    return storage.upload_file(filename, content, content_type)


def get_file_content(filename: str):
    """Read content from storage."""
    return storage.get_file_content(filename)


def find_file(paste_id: str):
    """Find a file by paste ID."""
    return storage.file_exists(paste_id)


def get_public_url(filename: str) -> str:
    """Get the public URL for a file."""
    return storage.get_public_url(filename)
