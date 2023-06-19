import requests
import subprocess
import re
import base64
filename = input("Enter final filename: ")
licenseurl = input("Enter license url: ")
mpd = input("Enter MPD url: ")

folder_path = f"ADDHERE" # make this a valid path, files will be downloaded to this location
dest_dir = f"{folder_path}/{filename}"

kid = requests.get(mpd)
result = re.search(r'cenc:default_KID="(\w{8}-(?:\w{4}-){3}\w{12})">', str(kid.text))
def get_pssh(keyId):
    array_of_bytes = bytearray(b'\x00\x00\x002pssh\x00\x00\x00\x00')
    array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
    array_of_bytes.extend(b'\x00\x00\x00\x12\x12\x10')
    array_of_bytes.extend(bytes.fromhex(keyId.replace("-", "")))
    return base64.b64encode(bytes.fromhex(array_of_bytes.hex()))

# Extract the encryption key ID from the regular expression match and generate the PSSH box
kid = result.group(1).replace('-', '')
assert len(kid) == 32 and not isinstance(kid, bytes), "wrong KID length"
pssh = format(get_pssh(kid).decode('utf-8'))
json_data = {
    'license': f'{licenseurl}',
    'headers': '',
    'pssh': f'{pssh}',                                                
    'buildInfo': '',                                                 
    'proxy': '',                                                      
    'cache': False,                                                    
}

# Send a POST request with the headers and JSON data to the specified URL
response = requests.post('https://cdrm-project.com/wv', json=json_data)
result = re.search(r"[a-z0-9]{16,}:[a-z0-9]{16,}", str(response.text))
decryption_key = result.group()
print(decryption_key)
decryption_key = f'key_id={decryption_key}'
decryption_key = decryption_key.replace(":",":key=")
download = subprocess.run(fr'N_m3u8DL-RE "{mpd}"--auto-select --save-name "{filename}" --auto-select --save-dir {folder_path} --tmp-dir {folder_path}/temp', shell=True, capture_output=True, text=True)
print(download)
decrypt = subprocess.run(fr'shaka-packager in="{folder_path}/{filename}.m4a",stream=audio,output="{dest_dir}/decrypted-audio.m4a" --enable_raw_key_decryption --keys {decryption_key}') 
print(decrypt)
decrypt = subprocess.run(fr'shaka-packager in="{folder_path}/{filename}.mp4",stream=video,output="{dest_dir}/decrypted-video.mp4" --enable_raw_key_decryption --keys {decryption_key}')
print(decrypt)
subprocess.run(["rm", f"{folder_path}/{filename}.m4a"])
subprocess.run(["rm", f"{folder_path}/{filename}.mp4"])
