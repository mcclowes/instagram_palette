# this code is messy but i'm feeling lazy. don't judge

import os, datetime, re, random, numpy, operator, cv2, colorsys
from sklearn.cluster import KMeans
from PIL import Image, ImageDraw
from collections import Counter

def debug(input):
  print(input)

# Settings
DEBUG = True
SAMPLE_IMAGE_X = 600
SAMPLE_IMAGE_Y = 400

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

def getBrightness(color):
  r, g, b = color
  h, s, v = colorsys.rgb_to_hsv(r,g,b)
  return v

def sortColors(colors):
  debug(colors)
  debug(sorted(colors, key=lambda color: getBrightness(color), reverse=True))
  # sort by brightness
  return sorted(colors, key=lambda color: getBrightness(color), reverse=True)

def extractColors(image, n):
  debug('> Extracting colors...')

  # shrink image for efficiency
  modified_image = cv2.resize(image, (SAMPLE_IMAGE_X, SAMPLE_IMAGE_Y), interpolation = cv2.INTER_AREA)
  #modified_image = image

  # reshape image into a list of pixels
  px_list = modified_image.reshape((modified_image.shape[0] * modified_image.shape[1], 3))

  # run kmeans function
  cluster = KMeans(n_clusters = n)

  debug('> Finding colors...')

  # find colors
  fit = cluster.fit(px_list)
  cluster_colors = fit.cluster_centers_.astype("uint8").tolist()

  debug('> Finding color frequencies...')

  # count colour frequencies
  labels = cluster.fit_predict(px_list)
  cluster_color_counts = Counter(labels)

  for i in range(0, len(cluster_colors)):
    cluster_colors[i] = [cluster_colors[i], cluster_color_counts[i]]

  debug('> Colors exracted...')

  return cluster_colors

def createBackgroundImage(colorPalette):
  r, g, b = [255, 255, 255]
  if(COLOR_BG==True):
    r, g, b = colorPalette[0][0]
  return Image.new("RGB", (CANVASS_SIZE, CANVASS_SIZE),(r, g, b))

def convertImages(input_files):
  # for every image in file list
  for i in input_files:
    if i == 'README.md':
      break

    # print state to terminal
    print("Converting " + i + '...')

    # open image and record size
    old_im = Image.open('input/' + i)
    old_im = old_im.convert('RGB')
    old_size = old_im.size
    old_x = old_size[0]
    old_y = old_size[1]

    # scale the image to have a 40 px buffer whether landscape or portrait
    scale = old_x / float(CANVAS_INNER)
    small_y = int(old_y / scale)

    # if y axis is too big to provide enough room underneath for blur
    # set up image for portrait 'mode'
    if small_y > (CANVASS_SIZE - (MARGIN * 4) - PALETTE_HEIGHT):
      new_scale = old_y / float(CANVAS_INNER)
      small_im = old_im.resize((int(old_x / new_scale), CANVAS_INNER), Image.ANTIALIAS)
      aspect = "portrait"
      # if there won't be enough room to right of image for portrait mode blur
      # escape and provide warning message
      if small_im.size[0] > (960 - PALETTE_HEIGHT):
        print("ya gonna have to crop this bad boi")
        break
    # else we're gonna be working in landscape
    else:
      small_im = old_im.resize((CANVAS_INNER, small_y), Image.ANTIALIAS)
      aspect = "landscape"

    # get small_im into a cv2 compatible format
    image = numpy.array(small_im)

    # calculate color palette
    colorPalette = extractColors(image, PALETTE_SIZE)
    debug(colorPalette)
    # create background image
    new_im = createBackgroundImage(colorPalette)

    # paste small_im onto background new_im
    new_im.paste(small_im, (MARGIN, MARGIN))
    draw = ImageDraw.Draw(new_im)

    debug('> Outputting...')

    # draw palette squares and fill with cluster colors
    position_buffer = MARGIN

    for j in range(0, PALETTE_SIZE):
      percentage = colorPalette[j][1] / (SAMPLE_IMAGE_X * SAMPLE_IMAGE_Y)
      color_width = percentage * AVAILABLE_SPACE

      left = position_buffer
      right = position_buffer + color_width

      position_buffer = position_buffer + color_width + MARGIN

      #left = MARGIN + (PALETTE_OFFSET * j)
      #right = PALETTE_OFFSET * (j + 1)

      if aspect == "landscape":
        draw.rectangle([left, PALETTE_INNER, right, PALETTE_OUTER], fill=tuple(colorPalette[j][0]), outline=None)
      else:
        draw.rectangle([PALETTE_INNER, left, PALETTE_OUTER, right], fill=tuple(colorPalette[j][0]), outline=None)

    # get modified date of original photo 
    # this allows the easy sorting of the output files by age of the original
    mtime = os.path.getmtime(os.getcwd() + '/input/' + i)
    str_mtime = datetime.datetime.isoformat(datetime.datetime.fromtimestamp(mtime))
    str_mtime = re.sub("[^0-9.]", "-", str_mtime)

    # save the new image and prefix name with modified date
    new_im.save('output/' + str_mtime + '_' + i)

    # print state to terminal
    print(i + ' converted')

# create a list of all non-hidden files in input folder
def listdir_nohidden(path):
  for f in os.listdir(path):
    if not f.startswith('.'):
      yield f

# create list of images in "input" directory
input_files = listdir_nohidden(os.getcwd() + '/input')
convertImages(input_files)
