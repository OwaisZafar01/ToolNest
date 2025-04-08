
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
import yt_dlp
import re
import os
import tempfile
import urllib.parse
import traceback
import logging
import uuid
import time

logger = logging.getLogger(__name__)

def download(request):
    url = request.GET.get('url', '').strip()
    video_info = {}
    error_message = None

    if url:
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            if any(domain in url for domain in ['youtube.com', 'youtu.be']):
                source_type = 'youtube'
            elif any(domain in url for domain in ['facebook.com', 'fb.watch']):
                source_type = 'facebook'
            elif any(domain in url for domain in ['instagram.com', 'instagr.am']):
                source_type = 'instagram'
            else:
                return render(request, 'download.html', {
                    'error_message': "Unsupported URL. Please enter a YouTube, Facebook, or Instagram URL.",
                    'url': url
                })

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'mp4',
                'socket_timeout': 15,
                'retries': 3,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                direct_url = None

                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        if not direct_url and 'url' in f:
                            direct_url = f.get('url')
                        formats.append({
                            'resolution': f'{f.get("height", "Unknown")}p',
                            'format_id': f.get('format_id'),
                            'ext': 'mp4',
                            'filesize': _format_filesize(f.get('filesize')),
                        })

                if not formats:
                    formats.append({
                        'resolution': 'Best Quality',
                        'format_id': 'best[ext=mp4]/best',
                        'ext': 'mp4',
                        'filesize': 'Unknown',
                    })

                formats.sort(
                    key=lambda x: _parse_resolution(x['resolution']),
                    reverse=True
                )

                formats = formats[:3]
                thumbnail = info.get('thumbnail', '')

                video_info = {
                    'title': info.get('title', f'{source_type.capitalize()} Video'),
                    'thumbnail': thumbnail,
                    'formats': formats,
                    'source': source_type,
                    'original_url': url,
                    'direct_url': direct_url,
                }

        except Exception as e:
            logger.error(f"Error processing URL {url}: {traceback.format_exc()}")
            error_message = f"Error processing video URL: {str(e)}"

    context = {
        'video_info': video_info,
        'error_message': error_message,
        'url': url
    }

    return render(request, 'download.html', context)

def download_file(request):
    url = request.GET.get('url', '')
    source = request.GET.get('source', '')
    format_id = request.GET.get('format_id', '')

    if not url:
        return HttpResponse("URL parameter is missing", status=400)

    temp_dir = tempfile.mkdtemp()

    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if source in ['youtube', 'facebook', 'instagram']:
            try:
                if source in ['facebook', 'instagram']:
                    format_id = 'best[ext=mp4]/best'

                ydl_info_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': format_id,
                    'socket_timeout': 15,
                    'retries': 3,
                }

                start_time = time.time()

                with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', f"{source}_video_{uuid.uuid4().hex[:8]}")
                    safe_title = _sanitize_filename(title)
                    ext = 'mp4'
                    temp_file_path = os.path.join(temp_dir, f"{safe_title}.{ext}")
                    final_filename = f"{safe_title}.{ext}"

                    download_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'format': format_id,
                        'outtmpl': temp_file_path,
                        'merge_output_format': 'mp4',
                        'restrictfilenames': True,
                        'socket_timeout': 30,
                        'retries': 5,
                        'fragment_retries': 5,
                        'continuedl': True,
                        'nooverwrites': False,
                    }

                    with yt_dlp.YoutubeDL(download_opts) as ydl_download:
                        ydl_download.download([url])

                    download_time = time.time() - start_time
                    logger.info(f"Download completed in {download_time:.2f} seconds")

                    if os.path.exists(temp_file_path):
                        with open(temp_file_path, 'rb') as f:
                            file_data = f.read()
                            response = HttpResponse(file_data, content_type='application/octet-stream')
                            encoded_filename = urllib.parse.quote(final_filename)
                            response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
                            response['Content-Length'] = len(file_data)
                            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                            response['Pragma'] = 'no-cache'
                            response['Expires'] = '0'
                            response['X-Content-Type-Options'] = 'nosniff'
                            return response
                    else:
                        logger.error(f"Downloaded file not found: {temp_file_path}")
                        return HttpResponse("Error: Downloaded file not found", status=404)

            except Exception as e:
                logger.error(f"Download error for {url}: {traceback.format_exc()}")
                return HttpResponse(f"Download failed: {str(e)}", status=500)

        else:
            return HttpResponse("Unsupported source", status=400)

    except Exception as e:
        logger.error(f"General download error: {traceback.format_exc()}")
        return HttpResponse(f"Download failed: {str(e)}", status=500)

    finally:
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {str(e)}")

def _sanitize_filename(filename):
    safe_name = re.sub(r'[^\w\s-]', '_', filename)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return safe_name[:50]

def _format_filesize(size):
    if size is None:
        return "Unknown"
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

def _parse_resolution(resolution):
    if resolution == "Unknown":
        return 0
    elif resolution == "Best Quality":
        return 9999
    try:
        return int(resolution.replace('p', ''))
    except ValueError:
        return 0
