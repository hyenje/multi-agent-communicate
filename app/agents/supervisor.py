from app.agents.critic import CriticAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.moderator import ModeratorAgent
from app.agents.persona_generator import PersonaGenerator
from app.agents.specialist import SpecialistAgent
from app.agents.synthesizer import SynthesizerAgent
from app.characters import assign_characters
from app.llm import LLMClient
from app.schemas import AgentMessage, SolveResponse


class Supervisor:
    def __init__(self, llm: LLMClient):
        self.persona_generator = PersonaGenerator(llm)
        self.moderator = ModeratorAgent(llm)
        self.specialist = SpecialistAgent(llm)
        self.critic = CriticAgent(llm)
        self.synthesizer = SynthesizerAgent(llm)
        self.evaluator = EvaluatorAgent(llm)
        self.llm = llm

    def solve(self, problem: str, persona_count: int, debate_rounds: int = 1) -> SolveResponse:
        personas, persona_message = self.persona_generator.generate(problem, persona_count)
        personas = assign_characters(personas)
        opening = self.moderator.open(problem, personas)
        specialist_messages = [self.specialist.answer(problem, persona) for persona in personas]
        discussion_messages: list[AgentMessage] = []

        messages: list[AgentMessage] = [persona_message, opening, *specialist_messages]

        for round_number in range(1, debate_rounds + 1):
            moderator_note = self.moderator.guide(
                problem=problem,
                personas=personas,
                transcript=self._format_transcript([*specialist_messages, *discussion_messages]),
                round_number=round_number,
            )
            messages.append(moderator_note)

            for persona in personas:
                response = self.specialist.respond(
                    problem=problem,
                    persona=persona,
                    transcript=self._format_transcript([*specialist_messages, *discussion_messages]),
                    moderator_note=moderator_note.content,
                    round_number=round_number,
                )
                discussion_messages.append(response)
                messages.append(response)

        debate_messages = [*specialist_messages, *discussion_messages]
        critique = self.critic.review(problem, debate_messages)
        synthesis = self.synthesizer.synthesize(problem, debate_messages, critique)
        evaluation = self.evaluator.evaluate(problem, debate_messages, critique, synthesis)

        messages.extend([critique, synthesis])
        used_llm = any(message.metadata.get("source") == "llm" for message in messages)
        return SolveResponse(
            problem=problem,
            personas=personas,
            messages=messages,
            final_answer=synthesis.content,
            evaluation=evaluation,
            used_llm=used_llm,
            model=self.llm.model,
        )

    def _format_transcript(self, messages: list[AgentMessage]) -> str:
        if not messages:
            return "아직 발언이 없습니다."
        return "\n\n".join(
            f"[{message.agent_name} / {message.role}]\n{message.content}"
            for message in messages
        )
