import requests
from tkinter import Tk, filedialog

def upload_file(file_path):
    upload_url = "https://store1.gofile.io/uploadFile"  # ใช้ URL ที่ถูกต้อง

    files = {
        'file': open(file_path, 'rb')
    }

    try:
        response = requests.post(upload_url, files=files)
        
        if response.status_code != 200:
            print(f"Failed to upload file. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return

        response_data = response.json()

        if response_data['status'] == 'ok':
            download_page = response_data['data']['downloadPage']
            print(f"File uploaded successfully! Download page: {download_page}")
        else:
            print(f"Failed to upload file. Error: {response_data['message']}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON response")
        print(f"Response: {response.text}")

if __name__ == '__main__':
    root = Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename()  # เปิด dialog สำหรับการเลือกไฟล์

    if file_path: 
        upload_file(file_path)
    else:
        print("No file selected.")
