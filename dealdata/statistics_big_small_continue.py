def analyze_data(data):
    if not data:
        return ""

    # 生成所有连续段的信息
    segments = []
    current_type = '小' if data[0] < 5 else '大'
    start = 0
    for i in range(1, len(data)):
        elem_type = '小' if data[i] < 5 else '大'
        if elem_type != current_type:
            segments.append({
                'type': current_type,
                'start': start,
                'end': i - 1,
                'length': i - start
            })
            current_type = elem_type
            start = i
    # 添加最后一个段
    segments.append({
        'type': current_type,
        'start': start,
        'end': len(data) - 1,
        'length': len(data) - start
    })

    # 筛选出长度≥5的段
    valid_segments = [seg for seg in segments if seg['length'] >= 8]

    if not valid_segments:
        return ""

    # 构建结果字符串
    result = []
    for i in range(len(valid_segments)):
        seg = valid_segments[i]
        result.append(f"[{seg['type']}({seg['length']})]")
        if i < len(valid_segments) - 1:
            next_seg = valid_segments[i + 1]
            gap = next_seg['start'] - seg['end'] - 1
        else:
            gap = len(data) - seg['end'] - 1
        result.append(str(gap))

    return '--'.join(result)

