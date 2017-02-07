from IPython.terminal.prompts import Prompts, Token

class CollectionPrompt(Prompts):
    """subclass of ipython terminal"""
    def in_prompt_token(self, cli=None):
        return [(Token, '(collection)-'),
                (Token.Prompt, 'In ['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, ']: ')
                ]
