FROM python:3.8

ARG USER_ID="1000"
ARG GROUP_ID="1000"
ARG HOME="/app/graph_learning"

ARG WORKFLOW
ENV WORKFLOW=${WORKFLOW}

ENV HOME=${HOME}
RUN groupadd --gid ${USER_ID} ${GROUP_ID} && \
    useradd --create-home --uid ${USER_ID} --gid ${GROUP_ID} --home-dir ${HOME} ${GROUP_ID}

WORKDIR ${HOME}

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chown -R ${USER_ID}:${GROUP_ID} ${HOME}
USER ${USER_ID}

CMD ["sh", "-c", "python3 main.py -w ${WORKFLOW}"]
