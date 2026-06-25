FROM ubuntu:25.10

RUN apt-get update \
    && apt-get install -y sudo curl git ca-certificates cmake ninja-build g++ lldb clang clang-format python3 \
        gettext qtbase5-dev libqt5svg5-dev libkf5archive-dev liblua5.3-dev libsqlite3-dev libsdl2-mixer-dev \
        pulseaudio-utils libpulse0 qt6-base-dev qt6-multimedia-dev qt6-svg-dev libkf6archive-dev \
    && usermod -l vscode -d /home/vscode -m ubuntu \
    && groupmod -n vscode ubuntu \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode

# FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# ARG USERNAME=vscode
# USER ${USERNAME}

# RUN sudo apt-get update \
#     && sudo apt-get install -y curl git cmake ninja-build g++ lldb python3 \
#         gettext qtbase5-dev libqt5svg5-dev libkf5archive-dev liblua5.3-dev libsqlite3-dev libsdl2-mixer-dev \
#         pulseaudio-utils libpulse0 software-properties-common
# # libkf6archive-dev

# RUN sudo apt-get install -y python3-pip \
#     && sudo pip3 install aqtinstall --break-system-packages \
#     && sudo mkdir -p /opt/qt6 \
#     && sudo aqt install-qt linux desktop 6.6.0 gcc_64 -O /opt/qt6

# RUN sudo add-apt-repository -y ppa:kubuntu-ppa/backports-extra \
#     && sudo apt-get update \
#     && sudo apt-get install -y libkf6archive-dev
    