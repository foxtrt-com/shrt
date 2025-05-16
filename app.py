# app.py
import logging
import pickle
import os
import random
import string

from flask import Flask, request, Response, redirect, render_template, jsonify

# Create Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def load_links(filename = 'links.pkl'):
    """Loads the links dict from the 'database'

    Args:
        filename (str, optional): Optional filename. Defaults to 'links.pkl'

    Returns:
        dict: Shortcodes and URIs
    """
    # If the 'database' exists, load the data
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            logging.info("Pickle db loaded.")
            return pickle.load(file)
    else:
        # Otherwise return an empty dict
        return {}

def save_link(shortcode, uri, filename = 'links.pkl'):
    """saves the links dict from the 'database'

    Args:
        shortcode (str): 4 character unique string
        uri (str): URI to link to
        filename (str, optional): Optional filename. Defaults to 'links.pkl'.
    """
    links[shortcode] = uri

    with open(filename, 'wb') as file:
        pickle.dump(links, file)

@app.route('/<shortcode>', defaults={'shortcode': None}, methods=['GET'])
@app.route('/', methods=['GET'])
def get(shortcode = None):
    """Get homepage or redirect to shortlink URI

    Args:
        shortcode (str, optional): If passed, will look up the shortcode to redirect.
    Returns:
        object: Either the index.html page, or a redirect code to the corresponding URI.
    """
    shortcode = request.url.strip(request.root_url)

    # If the shortcode exists, redirect to the URI
    if shortcode is not None and shortcode in links:
        logging.info("Redirected from shortcode")
        return redirect(links[shortcode])
    
    # Otherwise return the index page
    return render_template('index.html')

@app.route('/', methods=['POST'])
def post():
    """Post new URI data
    """
    uri = request.get_json()["uri"]

    # Return error if user does not pass a URI
    if uri is None:
        logging.info("uri parameter not passed.")
        return Response(str("uri parameter not passed."), status=400)
    
    # If uri has already been shortlinked, return the constructed shortlink for it
    try:
        return jsonify(request.root_url + [link_shortcode for link_shortcode, link_uri in links.items() if link_uri == uri][0])
    except IndexError:
        logging.info("Shortcode for URI does not exist")
        pass

    # Generate a unique 4 character shortcode
    for _ in range(1679616):
        shortcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) #1,679,616 possible permutations

        # If the shortcode has not been used then proceed, otherwise generate again
        if shortcode not in links:
            break

    # This is a check that will only trigger when the whole 4 character shortcode space has been used, and therefore cannot store more
    if shortcode in links:
        logging.error("Server out of shortcode storage!")
        return Response(str("Server out of storage."), status=500)

    # Save the shortcode to the 'database'
    logging.info("New shortcode saved.")
    save_link(shortcode, uri)
    # Return the constructed shortlink
    return jsonify(request.root_url + shortcode)

if __name__ == '__main__':
    links = load_links()
    logging.debug(links.items())
    app.run()