FROM diygod/rsshub:latest

# 安装 global-agent，构建时需要 devDependencies
RUN npm install -g global-agent && \
    cd /usr/local/lib/node_modules/global-agent && \
    npm install --legacy-peer-deps && \
    npm run build

# 使用自定义入口点来启动 RSSHub，确保 global-agent 被加载
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["npm", "start"]
