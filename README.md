# Automated YouTube Playlist | `auto_youtube_playlist`

[![GitHub last commit](https://img.shields.io/github/last-commit/Dyl-M/auto_youtube_playlist?label=Last%20commit&style=flat-square)](https://github.com/Dyl-M/auto_youtube_playlist/commits/main)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/Dyl-M/auto_youtube_playlist?label=Commit%20activity&style=flat-square)](https://github.com/Dyl-M/auto_youtube_playlist/commits/main)
[![DeepSource](https://deepsource.io/gh/Dyl-M/auto_youtube_playlist.svg/?label=active+issues&token=w_aZJJfhd5HPPLyXnDJkstmn)](https://deepsource.io/gh/Dyl-M/auto_youtube_playlist/?ref=repository-badge)
[![DeepSource](https://deepsource.io/gh/Dyl-M/auto_youtube_playlist.svg/?label=resolved+issues&token=w_aZJJfhd5HPPLyXnDJkstmn)](https://deepsource.io/gh/Dyl-M/auto_youtube_playlist/?ref=repository-badge)

[![Twitter Follow](https://img.shields.io/twitter/follow/dyl_m_tweets?label=%40dyl_m_tweets&style=social)](https://twitter.com/dyl_m_tweets)
[![Reddit User Karma](https://img.shields.io/reddit/user-karma/link/dyl_m?label=u%2Fdyl_m&style=social)](https://www.reddit.com/user/Dyl_M)

A project related to YouTube API. Add YouTube videos to playlists and update them automatically. This project will concern the following playlist:

- [🎧🔴 Music Livestreams](https://www.youtube.com/playlist?list=PLOMUdQFdS-XNaPVSol9qCUJvQvN5hO4hJ): Music radios on YouTube.
- [🎧 Mixes - Podcasts - Live performances](https://www.youtube.com/playlist?list=PLOMUdQFdS-XMJ4NFHJlSALYAt4l-LPgS1): Mixes, podcasts and live performances by a selection of DJs / musicians, labels and independent music curators.

Repository structure
-------------

Elements followed by `(IGNORED)` are kept ignored / hidden by git for privacy purpose or for being useless for code comprehension or workflow execution.

```
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── feature_request.yml
│   │   └── issue_report.yml
│   ├── workflows
│   │   ├── cron_workflow.yml
│   │   ├── licence_workflow.yml
│   │   └── update_workflow.yml
│   └── dependabot.yml
│
├── archive (IGNORED)
│   ├── 2022
│   │   ├── history_2022.log
│   │   └── mix_history_2022.csv
│   └── 2023
│       ├── history_20223.log
│       └── mix_history_2023.csv
│
├── cmd (IGNORED)
│
├── data
│   ├── add-on.json
│   ├── mix_history.csv
│   ├── playlists.json
│   └── pocket_tube.json
│
├── log 
│   ├── history.log
│   └── last_exe.log
│
├── notebooks
│   ├── .ipynb_checkpoints (IGNORED)
│   └── playlists_report.ipynb
│
├── src
│   ├── _sandbox.py
│   ├── analytics.py
│   ├── cron_update.py
│   ├── main.py
│   └── youtube_req.py
│
├── tokens (IGNORED)
│
├── .deepsource.toml
├── .gitignore
├── LICENSE
├── notes.txt
├── README.md
└── requirements.txt
```

External information
-------------

Codes are reviewed by the [DeepSource](https://deepsource.io/) bot.