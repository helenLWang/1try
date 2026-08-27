# Common Bugs and Solutions

## Connection Issues

### Error: `NoBrokersAvailable: NoBrokersAvailable`
**Problem**: Not connected to the Kafka server via SSH tunnel.

**Solution**:
1. Make sure you've established the SSH tunnel first:
   ```bash
   ssh -L <local_port>:localhost:<remote_port> <user>@<remote_server> -NTf
   ```
2. Verify the tunnel is active: `lsof -i :<local_port>` (should show ssh process)
3. Use the same port number in your `bootstrap_servers` parameter

---

### Error: `kcat` connection failures
```
% ERROR: Failed to query metadata for topic <topic_name>: Local: Broker transport failure
Connect to ipv6#[::1]:9092 failed: Connection refused
```

**Problem**: SSH tunnel not established before running kcat.

**Solution**:
- Always establish SSH tunnel BEFORE running kcat commands
- Use: `ssh -o ServerAliveInterval=60 -L 9092:localhost:9092 tunnel@<remote_server> -NTf`
- Verify connection with: `kcat -b localhost:9092 -L` (should list topics)

---

### Error: `Port already in use` or `Address already in use`
**Problem**: Another SSH tunnel is already using that port, or previous tunnel wasn't killed.

**Solution**:
1. Find and kill existing tunnel:
   ```bash
   lsof -ti:<local_port> | xargs kill -9
   ```
2. Or use a different local port in your SSH command

---

## Code Issues

### Error: `TypeError: a bytes-like object is required, not 'str'`
**Problem**: Trying to send string directly instead of bytes, or consumer trying to decode already-decoded data.

**Solution**:
- For Producer: Use `value_serializer=lambda v: json.dumps(v).encode('utf-8')` or `value_serializer=lambda m: dumps(m).encode('utf-8')`
- For Consumer: If producer used serializer, consumer needs `value_deserializer=lambda m: loads(m.decode('utf-8'))`. Otherwise, manually decode: `message.value.decode('utf-8')`

---

### Error: Consumer not reading messages / Consumer reads old messages
**Problem**: `auto_offset_reset` setting or consumer group behavior.

**Solution**:
- Use `auto_offset_reset='earliest'` to read from beginning
- Use `auto_offset_reset='latest'` to read only new messages
- If using same consumer group, Kafka remembers your offset. Either:
  - Use a different `group_id` each time, OR
  - Set `auto_offset_reset='earliest'` and `enable_auto_commit=False` for testing

---

### Error: `Topic does not exist` or `UnknownTopicOrPartitionException`
**Problem**: Topic hasn't been created yet, or wrong topic name.

**Solution**:
1. Make sure you ran the producer code first to create the topic
2. Verify topic exists: `kcat -b localhost:9092 -L` (lists all topics)
3. Check topic name spelling matches exactly (case-sensitive)

---

### Error: `AttributeError: 'dict' object has no attribute 'decode'`
**Problem**: Consumer code trying to decode when value_deserializer already decoded the message.

**Solution**:
- If using `value_deserializer` in consumer, `message.value` is already a dict, no need to decode/loads
- If NOT using deserializer, then decode: `message.value.decode('utf-8')` then `loads(...)`

---

## Offset and Seeking Issues

### Error: `IllegalStateError: No current assignment for partition -0`
**Problem**: You called `seek()` on a consumer that subscribed to a topic (topic passed to the constructor) but has not been assigned a partition yet. Assignment happens asynchronously during the group rebalance.

**Solution**:
- Use `consumer.assign([TopicPartition(topic, 0)])` instead of subscribing. Assignment is immediate, so `seek()` works right away. This is what the notebook's `explorer` consumer does.
- If you do want to subscribe, call `consumer.poll(timeout_ms=5000)` once first to force the rebalance, then `seek()`.

---

### Error: `OffsetOutOfRangeError`, or a seek that silently lands somewhere else
**Problem**: You seeked to an offset outside `[beginning_offsets, end_offsets)`. What happens next depends entirely on `auto_offset_reset`:
- `'earliest'` → silently resets to the log start offset
- `'latest'` → silently resets to the high watermark (so you read nothing until new messages arrive)
- `'none'` → raises `OffsetOutOfRangeError`

**Solution**: This is the intended behaviour, not a bug. Use `'none'` while experimenting so mistakes are loud rather than silent, and always clamp computed offsets into the valid range in production code.

---

### Error: `offsets_for_times()` returns `{TopicPartition(...): None}`
**Problem**: No message exists at or after the timestamp you asked for — usually because the timestamp is in the future, or is in seconds instead of **milliseconds**.

**Solution**:
1. Multiply by 1000: `int(time.time() * 1000)`, or `int(dt.timestamp() * 1000)` for a `datetime`.
2. Pick a timestamp inside your producer run. The record timestamps printed by the notebook (`record.timestamp`) and by `kcat -f "%o %T: %s\n"` are already in ms — copy one of those and adjust.
3. Always check for `None` before reading `.offset` off the result.

---

### Error: `poll()` returns `{}` / no messages after seeking
**Problem**: Either you seeked at or past the high watermark (there is nothing after it yet), or the timeout was too short for the first fetch.

**Solution**:
- Print `beginning_offsets()` and `end_offsets()` and confirm your target offset is `< end_offsets`.
- Give the first `poll()` a longer timeout (2000+ ms); the first call also has to fetch metadata.
- Remember `end_offsets()` is the offset of the *next* message to be written, so the last readable offset is `end_offsets - 1`.

---

### kcat: consumer hangs, or an offset returns fewer messages than expected
**Problem**: By default kcat keeps waiting for new messages once it reaches the end of the log, so a command that has already printed everything looks stuck. And a relative offset is capped by the log length.

**Solution**:
- Add `-e` to exit at the end of the log, and/or `-c N` to stop after N messages.
- Negative offsets are relative to the end, so `-o -50` on a 25-message topic just gives you all 25.
- An absolute offset at or past the high watermark prints nothing and waits — that is expected out-of-range behaviour, not a broken command.

---

## Environment Issues

### Error: `ModuleNotFoundError: No module named 'kafka'`
**Problem**: kafka-python not installed or wrong Python environment.

**Solution**:
1. Activate your virtual environment: `source <env_name>/bin/activate`
2. Install: `pip install kafka-python` or `pip install -r requirements.txt`
3. Verify: `python -c "from kafka import KafkaProducer; print('OK')"`

---

### Error: `kcat: command not found`
**Problem**: kcat not installed.

**Solution**:
- macOS: `brew install kcat`
- Ubuntu/Debian: `sudo apt-get install kcat`
- Windows: Use WSL or pair with someone on Mac/Linux for this deliverable

---

## General Troubleshooting Tips

1. **Always check SSH tunnel first**: `lsof -i :<your_port>` should show an ssh process
2. **Test connection**: Try `kcat -b localhost:9092 -L` to list topics before running Python code
3. **Check topic name**: Make sure producer and consumer use the exact same topic name
4. **Restart consumer**: If consumer seems stuck, stop it (Ctrl+C) and restart with a new group_id
5. **Verify data format**: Print `message.value` before processing to see what format you're getting
