# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar


from __future__ import unicode_literals

import os, requests, asyncio, math, time, wget
from pyrogram import filters, Client
from pyrogram.types import Message
from info import CHNL_LNK
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL

@Client.on_message(filters.command(['song', 'mp3']) & filters.private)
async def song(client, message):
    user_id = message.from_user.id 
    user_name = message.from_user.first_name 
    rpk = "["+user_name+"](tg://user?id="+str(user_id)+")"
    query = ''
    for i in message.command[1:]:
        query += ' ' + str(i)
    print(query)
    m = await message.reply(f"**ѕєαrchíng чσur ѕσng...!\n {query}**")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            return await m.edit("No results found. Try a different name.")
            
        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]       
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f'thumb_{user_id}.jpg'
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, 'wb').write(thumb.content)
        performer = f"VLCBox" 
        duration = results[0]["duration"]
        views = results[0]["views"]
    except Exception as e:
        print(str(e))
        return await m.edit("Example: /song vaa vaathi song")
                
    await m.edit("**Dᴏᴡɴʟᴏᴀᴅɪɴɢ чσur ѕσng...!**")
    audio_file = f"song_{user_id}.mp3"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_file,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        cap = f"**BY›› [VLCBOX]({CHNL_LNK})**"
        secmul, dur, dur_arr = 1, 0, duration.split(':')
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
            
        await message.reply_audio(
            audio_file,
            caption=cap,            
            quote=False,
            title=title,
            duration=dur,
            performer=performer,
            thumb=thumb_name
        )            
        await m.delete()
    except Exception as e:
        await m.edit(f"**🚫 Eʀʀᴏʀ: {e} 🚫**")
        print(e)
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)
        if os.path.exists(thumb_name):
            os.remove(thumb_name)

def get_text(message: Message) -> [None,str]:
    text_to_return = message.text
    if message.text is None:
        return None
    if " " not in text_to_return:
        return None
    try:
        return message.text.split(None, 1)[1]
    except IndexError:
        return None


@Client.on_message(filters.command(["video", "mp4"]))
async def vsong(client, message: Message):
    urlissed = get_text(message)
    if not urlissed:
        return await message.reply("Example: /video Your video link or name")     

    pablo = await client.send_message(message.chat.id, f"**𝙵𝙸𝙽𝙳𝙸𝙽𝙶 𝚈𝙾𝚄𝚁 𝚅𝙸𝙳𝙴𝙾** `{urlissed}`")
    
    try:
        search = SearchVideos(f"{urlissed}", offset=1, mode="dict", max_results=1)
        mi = search.result()
        if not mi["search_result"]:
            return await pablo.edit("No results found.")
        mio = mi["search_result"]
        mo = mio[0]["link"]
        thum = mio[0]["title"][:40]
        fridayz = mio[0]["id"]
        kekme = f"https://img.youtube.com/vi/{fridayz}/hqdefault.jpg"
        sedlyf = f"thumb_{message.from_user.id}.jpg"
        with open(sedlyf, "wb") as f:
            f.write(requests.get(kekme).content)
    except Exception as e:
        return await pablo.edit(f"Search failed: {e}")

    await pablo.edit("**Dᴏᴡɴʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ...**")
    file_stark = f"video_{message.from_user.id}.mp4"
    opts = {
        "format": "best",
        "outtmpl": file_stark,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
    }
    
    try:
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(mo, download=True)
    except Exception as e:
        return await pablo.edit_text(f"**𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍 𝙵𝚊𝚒𝚕𝚎𝚍** \n**Error :** `{str(e)}`")       
    
    capy = f"**𝚃𝙸𝚃𝙻𝙴 :** [{thum}]({mo})\n**𝚁𝙴𝚀𝚄𝙴𝚂𝚃𝙴𝙳 𝙱𝚈 :** {message.from_user.mention}"

    try:
        await client.send_video(
            message.chat.id,
            video=file_stark,
            duration=int(ytdl_data["duration"]),
            file_name=str(ytdl_data["title"]),
            thumb=sedlyf,
            caption=capy,
            supports_streaming=True,        
            reply_to_message_id=message.id 
        )
        await pablo.delete()
    except Exception as e:
        await pablo.edit(f"Failed to send video: {e}")
    finally:
        if os.path.exists(file_stark):
             os.remove(file_stark)
        if os.path.exists(sedlyf):
             os.remove(sedlyf)
