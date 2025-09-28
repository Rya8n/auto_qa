import os
import base64
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By

MAIN = "_main_article"
COMMENT = "_comment"

def scrape_element_with_images_with_css(driver, element_type, selector=".comment:nth-child(1) .comment-text", idx=""):
    try:
        # Find the comment element
        comment_element = driver.find_element(By.CSS_SELECTOR, selector)
        
        # Find all child elements (paragraphs, divs, etc.) that contain text or images
        child_elements = comment_element.find_elements(By.XPATH, "./*")
        
        text_parts = []
        image_urls = []
        image_counter = 0
        
        for element in child_elements:
            nodes = driver.execute_script("""
                var element = arguments[0];
                var result = [];
                
                function processNode(node) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        var text = node.textContent.trim();
                        if (text) {
                            result.push({type: 'text', content: text});
                        }
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName.toLowerCase() === 'img') {
                            result.push({type: 'image', content: node.src});
                        } else {
                            // Recursively process child nodes
                            for (var i = 0; i < node.childNodes.length; i++) {
                                processNode(node.childNodes[i]);
                            }
                        }
                    }
                }
                
                for (var i = 0; i < element.childNodes.length; i++) {
                    processNode(element.childNodes[i]);
                }
                
                return result;
            """, element)
            
            for node in nodes:
                if node['type'] == 'text':
                    text_parts.append(node['content'])
                elif node['type'] == 'image':
                    text_parts.append("image_"+str(image_counter)+element_type+idx)
                    image_urls.append(node['content'])
                    image_counter += 1
        
        final_text = ' '.join(text_parts)
        
        return {
            "text": final_text,
            "images": image_urls
        }
        
    except Exception as e:
        print(f"Error scraping comment: {e}")
        return {"text": "", "images": []}

def download_image(downloaded_images, image_url, filename):
    try:
        # Send GET request to download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Save the image
        full_filename = filename + '.png'
        with open(full_filename, 'wb') as f:
            f.write(response.content)
        
        # Add to list for later cleanup
        downloaded_images.append(full_filename)
        return True
        
    except Exception as e:
        print(f"Error downloading image {filename}: {e}")
        return False

def download_images_from_result(downloaded_images, result_dict, element_type, idx=""):
    if 'images' in result_dict and result_dict['images']:
        for i, image_url in enumerate(result_dict['images']):
            # Generate filename based on the pattern used in text
            filename = f"image_{i}{element_type}{idx}"
            download_image(downloaded_images, image_url, filename)
    
    return result_dict

def list_png_files(folder_path):
    try:
        png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        return png_files
    except FileNotFoundError:
        print("Path does not exist.")
        return []

def convert_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def cleanup_downloaded_images(downloaded_images):
    for filename in downloaded_images:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            pass
