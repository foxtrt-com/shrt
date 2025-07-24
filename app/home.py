# home.py
import logging
import pickle
import os
import random
import string

from flask import Blueprint, request, Response, redirect, render_template, jsonify, current_app

bp = Blueprint('home', __name__)

def load_links(filename = None):
    """Loads the links dict from the 'database'

    Args:
        filename (str, optional): Optional filename. Defaults to 'links.pkl'

    Returns:
        dict: Shortcodes and URIs
    """
    if filename == None:
        filename = os.path.join(current_app.instance_path, 'links.pkl')

    # If the 'database' exists, load the data
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            logging.info("Pickle db loaded.")
            return pickle.load(file)
    else:
        # Otherwise return an empty dict
        return {}

def save_link(shortcode, uri, filename = None):
    """saves the links dict from the 'database'

    Args:
        shortcode (str): 4 character unique string
        uri (str): URI to link to
        filename (str, optional): Optional filename. Defaults to 'links.pkl'.
    """
    if filename == None:
        filename = os.path.join(current_app.instance_path, 'links.pkl')

    links = load_links()
    
    links[shortcode] = uri

    with open(filename, 'wb') as file:
        pickle.dump(links, file)

@bp.route('/<shortcode>', defaults={'shortcode': None}, methods=['GET'])
@bp.route('/', methods=['GET'])
def get(shortcode = None):
    """Get homepage or redirect to shortlink URI

    Args:
        shortcode (str, optional): If passed, will look up the shortcode to redirect.
    Returns:
        object: Either the index.html page, or a redirect code to the corresponding URI.
    """
    shortcode = request.url.strip(request.root_url)
    links = load_links()

    # If the shortcode exists, redirect to the URI
    if shortcode is not None and shortcode in links:
        logging.info("Redirected from shortcode")
        return redirect(links[shortcode])
    
    # Otherwise return the index page
    return render_template('index.html')

@bp.route('/', methods=['POST'])
def post():
    """Post new URI data
    """
    json = request.get_json()
    uri = json["uri"]
    shortcode = json["shortcode"]
    links = load_links()

    # Return error if user does not pass a URI
    if uri is None:
        logging.info("uri parameter not passed.")
        return Response(str("uri parameter not passed."), status=400)

    # If user defined shortcode exists, return error
    if shortcode in links:
        logging.info("shortlink parameter already in use.")
        return Response(str("shortlink parameter already in use."), status=400)
    elif shortcode is not None and shortcode != '':
        # Save the shortcode to the 'database'
        logging.info("New shortcode saved.")
        save_link(shortcode, uri)
        # Return the constructed shortlink
        return jsonify(request.root_url + shortcode)
    
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