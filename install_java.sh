#!/bin/bash

# Example of running the script: install-java.sh 8u131 1.8.0_131 mycompany dev
# The script assumes you are hosting the java installation files by yourself internaly in AWS s3 bucket

# Need to be adjusted if you are running debian/ubuntu distro
remove_current_java(){
    yum -y remove java*
}

download_java(){
    mkdir -p /usr/local/java/
    cd /usr/local/java/
    echo "Downloading file from: s3://${COMPANY}-devops-${ENV_TYPE}/server-components/java/jdk-${JAVA_PACKAGE_VER}-linux-x64.tar.gz"
    aws s3 cp s3://${COMPANY}-devops-${ENV_TYPE}/server-components/java/jdk-${JAVA_PACKAGE_VER}-linux-x64.tar.gz /usr/local/java/jdk-${JAVA_PACKAGE_VER}-linux-x64.tar.gz
}

deploy_java(){
    tar -xvzf jdk-${JAVA_PACKAGE_VER}-linux-x64.tar.gz > /dev/null
    rm -rf /usr/bin/java
    ln -s /usr/local/java/jdk${JDK_VER}/bin/java /usr/bin/java
}

setup_java_home(){
    echo "export JAVA_HOME=/usr/local/java/jdk${JDK_VER}" >> /etc/bashrc
    echo 'export PATH=$PATH:$JAVA_HOME/bin' >> /etc/bashrc
}

deploy_cleanup(){
    rm -rf /usr/local/java/jdk-${JAVA_PACKAGE_VER}-linux-x64.tar.gz
}

start_time=`date +%s`

JAVA_PACKAGE_VER=${1}
JDK_VER=${2}
COMPANY=${3}
ENV_TYPE=${4}

remove_current_java
download_java
deploy_java
setup_java_home
deploy_cleanup

end_time=`date +%s`
echo execution time was `expr ${end_time} - ${start_time}` s.
