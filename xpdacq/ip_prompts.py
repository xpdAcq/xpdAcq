from IPython.terminal.prompts import Prompts, Token

class CollectionPrompts(Prompts):
    def in_prompt_token(self, cli=None):
        return [(Token, '(collection-)'),
                (Token.Prompt, 'In['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, ']: ')]
