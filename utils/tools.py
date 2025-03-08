import os
import io
import requests
import json
import webbrowser
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from urllib.parse import urlencode

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

####################
## LINKEDIN TOOLS ##
####################

def get_authorization_code(linkedin_client_id, linkedin_redirect_uri, scope="r_liteprofile r_emailaddress w_member_social"):
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

def get_refresh_token(linkedin_client_id, linkedin_client_secret, authorization_code, linkedin_redirect_uri):
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

def get_access_token(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token):
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

def get_urn(access_token):
    """Retrieve LinkedIn URN using an access token."""
    post_url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    response = requests.get(post_url, headers=headers)

    urn = json.loads(response.content.decode('utf-8'))['id']
    return urn
    
def upload_image(image, access_token, author_urn):
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

    # test image upload
    #image_path = '/Users/anthonychamberas/Downloads/lip.jpg'
    #with open(image_path, 'rb') as image_file:
    #    requests.put(upload_url, data=image_file, headers={"Authorization": f"Bearer {access_token}"})

    # save image to buffer
    # image_bytes = image.tobytes()
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()

    requests.put(upload_url, data=image_bytes, headers={"Authorization": f"Bearer {access_token}"})
    
    return asset_urn

def post_to_linkedin(text, image, linkedin_client_id, linkedin_client_secret, linkedin_refresh_token):
    """Post a text update with an image to LinkedIn."""

    access_token = get_access_token(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token)
    if not access_token:
        print(linkedin_client_id, linkedin_client_secret, linkedin_refresh_token)
        print("Failed to obtain LinkedIn access token.")
        return

    author_urn = get_urn(access_token)
    asset_urn = upload_image(image, access_token, author_urn)
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

    print(author_urn, text, asset_urn)

    response = requests.post(post_url, headers=headers, json=post_data)

    print(response.content)

    return response.content

