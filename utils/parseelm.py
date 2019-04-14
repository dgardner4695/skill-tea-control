
class Newline(object):
	def __init__(self):
		pass

newline = Newline()

def tokenized(lines):
	insert_newline = False
	for line in lines:
		if not insert_newline:
			insert_newline = True
		else:
			yield newline
		for token in line.split():
			stripped = token.strip()
			if stripped:
				yield stripped

def parse_response(response, strict=True):
	stripped = response.strip()
	if not response:
		raise ValueErorr(
			"Unexpected empty response from ELM327. (note response was {})".format(repr(response))
		)
	cleaned = response.replace("SEARCHING...", "")
	lines = tuple((line.strip() for line in cleaned.split('\r') if line.strip()))
	if not lines:
		fmt = "Expected at least one carriage return in response from ELM327. (note response was {})"
		raise ValueError(fmt.format(repr(response)))
	if response[0] == '4':
		yield from parse_single_line_response(tokenized(lines), response, strict)
	elif response[0] == '0':
		yield from parse_multiline_response(tokenized(lines), response, strict)
	else:
		raise ValueError(
			"Expected '0' (multiline) or '4' (single line) as first character in response"
			+ " but got {} instead.  (note response was {})".format(repr(response[0]), repr(response))
		)

def parse_single_line_response(tokens, resp, strict):
	assert resp and resp[0] == '4'
	ended_line = False
	got_chevron = False
	for t in tokens:
		if ended_line and got_chevron and strict:
			raise ValueError(
				"Unexpected extra token, {}, after '>' in single-line response from elm327. (note response was {})".format(repr(t), repr(resp))
			)
		elif ended_line:
			if t != ">" and strict:
				raise ValueError(
					"Expected '>' after newline in single-line response from elm327 but got '{}' instead.".format(repr(t))
					+ " (note response was {})".format(repr(resp))
				)
			got_chevron = True
		elif t is newline:
			ended_line = True
		else:
			yield int(t, 16)

def parse_multiline_response(tokens, resp, strict):
	tokens = iter(tokens)
	try:
		expected_token_count = int(next(tokens), 16)
	except StopIteration:
		assert False, "at least one token ought to be there"
	expected_line = 0
	done = False
	token_count = 0
	while True:
		try:
			line_number_str = next(tokens)
		except StopIteration:
			break
		if done:
			raise ValueError(
				"Unexpected extra data after '>' in multiline response from elm327."
				+ " (note response was {})".format(repr(resp))
			)
		elif line_number_str == '>':
			done = True
			continue
		elif not line_number_str or line_number_str[-1] != ':':
			raise ValueError(
				"Expected line number or '>' after newline in single-line response"
				+ " from elm327 but got '{}' instead.".format(repr(line_number_str))
				+ " (note response was {})".format(repr(resp))
			)
		try:
			line_number = int(line_number_str[:-1], 16)
		except ValueError:
			raise ValueError(
				"Expected line number or '>' after newline in multiline response"
				+ " from elm327 but got '{}' instead.".format(repr(line_number_str))
				+ " (note response was {})".format(repr(resp))
			)
		if line_number != expected_line:
			raise ValueError(
				("Expected line '{}' but got '{}' newline in multiline response"
				+ " from elm327. (note response was {})").format(expected_line, line_number, repr(resp))
			)
		break_again = False
		while True:
			try:
				tok = next(tokens)
			except StopIteration:
				break_again = True
				break
			if tok == newline:
				break
			yield int(tok, 16)
			token_count += 1
		if break_again:
			break
		expected_line += 1
		expected_line %= 16
		

	if token_count != expected_token_count:
		raise ValueError(
			"Expected '{}' values but got '{}' in multiline response from ELM327.".format(
				expected_token_count,
				token_count
			)
		)

			



