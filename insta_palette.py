# this code is messy but i'm feeling lazy. don't judge

import os, datetime, re, random, numpy, operator, cv2, colorsys
from sklearn.cluster import KMeans
from PIL import Image, ImageDraw
from collections import Counter

# --------------------------------------------

# Config

DEBUG = True
SAMPLE_IMAGE_X = 600
SAMPLE_IMAGE_Y = 400
SORT_BY_SATURATION = True

# Image settings
COLOR_BG = True
PALETTE_SIZE = 7

# Dimensions
MARGIN = 40
CANVASS_SIZE = 1080
CANVAS_INNER = CANVASS_SIZE - (MARGIN * 2)

PALETTE_HEIGHT = (CANVAS_INNER - (MARGIN * (PALETTE_SIZE - 1))) / PALETTE_SIZE
PALETTE_OFFSET = PALETTE_HEIGHT + MARGIN
PALETTE_INNER = 872
PALETTE_OUTER = CANVASS_SIZE - MARGIN

AVAILABLE_SPACE = CANVAS_INNER - (MARGIN * (PALETTE_SIZE - 1))

# --------------------------------------------

# Utility functions

def debug(input):
  print(input)

def getBrightness(color):
  r, g, b = color
  h, s, v = colorsys.rgb_to_hsv(r,g,b)
  return v

def getSaturation(color):
  r, g, b = color
  h, s, v = colorsys.rgb_to_hsv(r,g,b)
  return s

def sortColors(colors):
  if SORT_BY_SATURATION == True:
    return sorted(colors, key=lambda color: getSaturation(color), reverse=True)
  else: 
    return sorted(colors, key=lambda color: getBrightness(color), reverse=True)

# exif metadata
# orientation = 6
def extractMetadata(image):
  return {
    ExifTags.TAGS[k]: v
    for k, v in image._getexif().items()
    if k in ExifTags.TAGS
  }

# --------------------------------------------

# Functions

def extractColors(image, n):
  debug('> Extracting colors...')
  # shrink image for efficiency
  modified_image = cv2.resize(image, (SAMPLE_IMAGE_X, SAMPLE_IMAGE_Y), interpolation = cv2.INTER_AREA)
  # reshape image into a list of pixels
  px_list = modified_image.reshape((modified_image.shape[0] * modified_image.shape[1], 3))
  # run kmeans function
  cluster = KMeans(n_clusters = n)

  debug('> Finding colors...')
  # find colors
  fit = cluster.fit(px_list)
  cluster_colors = fit.cluster_centers_.astype("uint8").tolist()
  debug(cluster_colors)
  #cluster_colors = sortColors(cluster_colors)

  debug('> Finding color frequencies...')
  # count colour frequencies
  labels = cluster.fit_predict(px_list)
  debug(labels)
  cluster_color_counts = Counter(labels)
  debug(cluster_color_counts)

  for i in range(0, len(cluster_colors)):
    cluster_colors[i] = [cluster_colors[i], cluster_color_counts[i]]

  debug('> Colors exracted...')
  return cluster_colors

def createBackgroundImage(color_palette):
  r, g, b = [255, 255, 255]

  if(COLOR_BG == True):
    r, g, b = color_palette[0][0]
  return Image.new("RGB", (CANVASS_SIZE, CANVASS_SIZE),(r, g, b))

def isPortrait(original_image):
  # scale image
  scale = original_image.size[0] / float(CANVAS_INNER) # have a 40 px buffer whether landscape or portrait    
  small_y = int(original_image.size[1] / scale)

  # if y axis is too big to provide enough room underneath for blur
  if small_y > (CANVASS_SIZE - (MARGIN * 4) - PALETTE_HEIGHT):
    return True # set up image for portrait 'mode'
  else: # else we're gonna be working in landscape
    return False

def scaleImage(Image, aspect_portrait, original_image):
  # scale image
  scale = original_image.size[0] / float(CANVAS_INNER) # have a 40 px buffer whether landscape or portrait    
  small_y = int(original_image.size[1] / scale)

  original_x = original_image.size[0]
  original_y = original_image.size[1]

  if aspect_portrait == True:
    new_scale = original_y / float(CANVAS_INNER)
    return original_image.resize((int(original_x / new_scale), CANVAS_INNER), Image.ANTIALIAS)
  else: 
    return original_image.resize((CANVAS_INNER, small_y), Image.ANTIALIAS)

def drawPalette(draw, color_palette, aspect_portrait):
  position_buffer = MARGIN

  # draw palette squares and fill with cluster colors
  for j in range(0, PALETTE_SIZE):
    percentage = color_palette[j][1] / (SAMPLE_IMAGE_X * SAMPLE_IMAGE_Y)
    color_width = percentage * AVAILABLE_SPACE

    left = position_buffer
    right = position_buffer + color_width

    position_buffer = position_buffer + color_width + MARGIN

    if aspect_portrait == True:
      draw.rectangle([PALETTE_INNER, left, PALETTE_OUTER, right], fill=tuple(color_palette[j][0]), outline=None)
    else:
      draw.rectangle([left, PALETTE_INNER, right, PALETTE_OUTER], fill=tuple(color_palette[j][0]), outline=None)

def convertImages(input_files):
  for i in input_files:
    if i == 'README.md':
      break

    print("Converting " + i + '...')

    # open image and record size
    original_image = Image.open('input/' + i).convert('RGB')

    aspect_portrait = isPortrait(original_image)
    small_im = scaleImage(Image, aspect_portrait, original_image)

    # if there won't be enough room to right of image for portrait mode blur escape and provide warning message
    if(aspect_portrait == True & small_im.size[0] > (960 - PALETTE_HEIGHT)):
      print("Ya gonna have to crop this bad boi")
      break

    # get small_im into a cv2 compatible format
    image = numpy.array(small_im)

    # calculate color palette
    color_palette = extractColors(image, PALETTE_SIZE)

    debug('> Drawing...')
    # create background image
    new_im = createBackgroundImage(color_palette)    
    new_im.paste(small_im, (MARGIN, MARGIN)) # paste small_im onto background new_im

    draw = ImageDraw.Draw(new_im)
    drawPalette(draw, color_palette, aspect_portrait)

    debug('> Outputting...')
    # get modified date of original photo 
    mtime = os.path.getmtime(os.getcwd() + '/input/' + i)
    str_mtime = datetime.datetime.isoformat(datetime.datetime.fromtimestamp(mtime))
    str_mtime = re.sub("[^0-9.]", "-", str_mtime)
    # save the new image and prefix name with modified date
    new_im.save('output/' + str_mtime + '_' + i)
    # print state to terminal
    print(i + ' converted')

# iterate over inputs
def listdir_nohidden(path):
  for f in os.listdir(path):
    if not f.startswith('.'):
      yield f

# --------------------------------------------

# create list of all non-hidden files in input folder in "input" directory
input_files = listdir_nohidden(os.getcwd() + '/input')
convertImages(input_files)
