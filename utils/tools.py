import os
import io
import requests
import json
import webbrowser
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from urllib.parse import urlencode
from utils.markdown_to_ricos import convert_markdown_to_ricos

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'creds/gristmill5-e521e2f08f35.json'

def adjust_image_exposure(img, factor):

    # Adjusts the exposure of an image.
    enhancer = ImageEnhance.Brightness(img)
    adjusted_image = enhancer.enhance(factor/100)

    return adjusted_image


def text_on_image(img, text, margin=10, font_size=60):

    draw = ImageDraw.Draw(img)

    font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

    font = ImageFont.truetype(font_path, font_size)

    text_color = (255, 255, 255)

    max_width = img.width - 2 * margin
    wrapped_lines = textwrap.wrap(text, width=max_width // (font_size // 2)) # Approximation for character width

    text_height = font.getbbox(text)[3] 
    total_text_height = len(wrapped_lines) * (text_height + 10)

    y_text = (img.height - total_text_height) // 5
    
    for line in wrapped_lines:
        line_width = font.getlength(line)
        x_text = (img.width - line_width) // 2
        draw.text((x_text, y_text), line, font=font, fill=text_color)
        y_text += text_height + 10

    # place logo on image
    logo = Image.open('/Users/anthonychamberas/Projects/agentic/static/logo.png', 'r')
    logo_w, logo_h = logo.size
    img_w, img_h = img.size
    # offset = ((img_w - logo_w) // 2, (img_h - logo_h) // 2)
    offset = ((img_w - logo_w) // 2, 7* (img_h - logo_h) // 8)
    img.paste(logo, offset, logo)

    return img

def crop_image(img, left=0, top=50, right=800, bottom=510):
    img_cropped = img.crop((left, top, right, bottom))
    return img_cropped

def image_to_bytes(img):
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()

    return img_bytes

def generate_ricos(markdown_text):
    """
    Convert markdown text to RICOS format.
    
    Args:
        markdown_text (str): The markdown text to convert
        
    Returns:
        dict: A RICOS document
    """
    converter = MarkdownToRicosConverter()
    return converter.convert(markdown_text)

####################
## LINKEDIN TOOLS ##
####################

def get_linkedin_authorization_code(linkedin_client_id, linkedin_redirect_uri, scope="r_liteprofile r_emailaddress w_member_social"):
    """Generate the LinkedIn authorization URL and open it in a browser to obtain the authorization code."""
    auth_url = "https://www.linkedin.com/oauth/v2/authorization"
    params = {
        "response_type": "code",
        "client_id": linkedin_client_id,
        "redirect_uri": linkedin_redirect_uri,
        "state":"abcdefghi123456",
        "scope": scope
    }
    url = f"{auth_url}?{urlencode(params)}"
    webbrowser.open(url)
    print("Please authorize the app and enter the authorization code from the redirected URL.")

def get_linkedin_refresh_token(linkedin_client_id, linkedin_client_secret, authorization_code, linkedin_redirect_uri):
    """Retrieve LinkedIn OAuth refresh token using an authorization code."""
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": linkedin_redirect_uri,
        "client_id": linkedin_client_id,
        "client_secret": linkedin_client_secret
    }
    response = requests.post(token_url, data=data, headers=headers)
    tokens = response.json()

    print(response.content)
    
    return tokens.get("refresh_token"), tokens.get("access_token")

def get_linkedin_access_token(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token):
    """Retrieve LinkedIn OAuth access token using a refresh token."""
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "refresh_token",
        "client_id": linkedin_client_id,
        "client_secret": linkedin_client_secret,
        "refresh_token": linkedin_refresh_token
    }
    response = requests.post(token_url, data=data)

    access_token = response.json().get("access_token")
    return access_token

def get_linkedin_urn(access_token):
    """Retrieve LinkedIn URN using an access token."""
    post_url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    response = requests.get(post_url, headers=headers)

    urn = json.loads(response.content.decode('utf-8'))['id']
    return urn
    
def post_linkedin_image(image, access_token, author_urn):
    """Upload an image to LinkedIn and return the asset URN."""
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    upload_request = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{author_urn}",
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    
    response = requests.post(register_url, headers=headers, json=upload_request)
    response_data = response.json()
    upload_url = response_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = response_data['value']['asset']

    # save image to bytes
    image_bytes = image_to_bytes(image)

    requests.put(upload_url, data=image_bytes, headers={"Authorization": f"Bearer {access_token}"})
    
    return asset_urn

def post_linkedin_post(text, image, linkedin_client_id, linkedin_client_secret, linkedin_refresh_token):
    """Post a text update with an image to LinkedIn."""

    access_token = get_linkedin_access_token(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token)
    if not access_token:
        print(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token)
        print("Failed to obtain LinkedIn access token.")
        return

    author_urn = get_linkedin_urn(access_token)
    asset_urn = post_linkedin_image(image, access_token, author_urn)
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    post_data = {
        "author": f"urn:li:person:{author_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Image description"
                        }, 
                        "media": asset_urn
                    }
                ]

            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    response = requests.post(post_url, headers=headers, json=post_data)

    print(response.content)

    return response.content

###############
## WIX TOOLS ##
###############

def post_wix_blog(wix_site_id, wix_api_key, wix_member_id, post, image, publish=False):

    # crop image and save to bytes
    image_cropped = crop_image(image, 0, 50, 800, 510)
    image_bytes = image_to_bytes(image_cropped)

    # extract title and text from post
    title = post.split('\n')[0]
    title = title if title else "Untitled"

    text = post.split('\n')[1:]

    image_response = post_wix_image(image_bytes, wix_site_id, wix_api_key, f"{title}.png")
    image_id = image_response["file"]["id"]
    image_url = image_response["file"]["url"]

    post_url = "https://www.wixapis.com/blog/v3/draft-posts/"

    headers = {
        "Authorization": wix_api_key, 
        "wix-site-id": wix_site_id,
        "Content-Type": "application/json"
    }

    post_data = {
        "publish": publish,
        "draftPost": {
            "title": title,
            "featured": True,
            "coverMedia": {
                "enabled": True,
                "image": {
                    "id": image_id,
                    "url": image_url,
                    "height": 460,
                    "width": 800,
                },
                "displayed": True,
                "custom": True
            },
        "memberId": wix_member_id,
        "commentingEnabled": True,
        "heroImage": {
            "id": image_id,
            "url": image_url,
            "altText": title
        },
        "language": "en",
        },
        "fieldsets": ["URL", "RICH_CONTENT"]
    }

    image_block = {
        "type": "IMAGE",
        "id": "",
        "nodes": [],
        "imageData": {
            "image": {
                "src": {
                    "url": image_url,
                    "height": 460,
                    "width": 800,
                    "private": False,
                    "id": image_id
                }
            }
        }
    }

    post_data["draftPost"]["richContent"] = convert_markdown_to_ricos(post)["richContent"]
    post_data["draftPost"]["richContent"]["nodes"].append(image_block)

    response = requests.post(post_url, headers=headers, json=post_data)

    print(response.content)

    return response.content

def post_wix_image(image, wix_site_id, wix_api_key, filename="image.png"):

    # Step 1: Get Upload URL
    upload_url_endpoint = "https://www.wixapis.com/site-media/v1/files/generate-upload-url"

    headers = {
        "Authorization": wix_api_key, 
        "wix-site-id": wix_site_id,
        "Content-Type": "application/json"
    }

    data = {
        "mimeType": "image/png",
        "filename": filename
    }

    response = requests.post(upload_url_endpoint, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        upload_url_data = response.json()
        upload_url = upload_url_data["uploadUrl"]

        # Step 2: Upload the image
        upload_headers = {'Content-Type': 'image/jpeg'}  # Adjust content type if needed
        upload_response = requests.put(upload_url, headers=upload_headers, data=image, params=data)

        if upload_response.status_code == 200:
            print("Image uploaded successfully!")
            return upload_response.json()
        else:
            message = {
                "status":"failure",
                "code": upload_response.status_code,
                "message": f"file upload failed: {upload_response.text}"
            }

            return message
    else:
        message = {
            "status":"failure",
            "code": upload_response.status_code,
            "message": f"upload url failed: {upload_response.text}"
        }

        return message
