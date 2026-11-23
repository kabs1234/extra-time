export type Page<TItem> = {
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: ReadonlyArray<TItem>;
};

export type Profile = {
  readonly favorite_club: string;
  readonly country: string;
  readonly bio: string;
};

export type Stats = {
  readonly attempts: number;
  readonly total_correct: number;
  readonly best_score_pct: number;
};

export type Me = {
  readonly id: number;
  readonly username: string;
  readonly date_joined: string;
  readonly profile: Profile;
  readonly stats: Stats;
};

export type LoginResponse = {
  readonly access: string;
  readonly user: Me;
};

export type AccessToken = {
  readonly access: string;
};

export type SignupInput = {
  readonly username: string;
  readonly password: string;
  readonly favorite_club?: string;
  readonly country?: string;
};

export type MeInput = {
  readonly username?: string;
  readonly profile?: Partial<Profile>;
};

export type Era = {
  readonly id: number;
  readonly name: string;
  readonly start_year: number;
  readonly end_year: number;
  readonly summary: string;
};

export type Topic = {
  readonly id: number;
  readonly name: string;
  readonly slug: string;
  readonly description: string;
};

export const Difficulty = {
  Easy: 'easy',
  Medium: 'medium',
  Hard: 'hard',
} as const;

export type Difficulty = (typeof Difficulty)[keyof typeof Difficulty];

export type Choice = {
  readonly id: number;
  readonly text: string;
  readonly is_correct?: boolean;
};

export type Question = {
  readonly id: number;
  readonly text: string;
  readonly difficulty: Difficulty;
  readonly explanation?: string;
  readonly era: number;
  readonly era_name: string;
  readonly topics: ReadonlyArray<number>;
  readonly topic_names: ReadonlyArray<string>;
  readonly author: string;
  readonly choices: ReadonlyArray<Choice>;
  readonly created_at: string;
  readonly updated_at: string;
};

export type ChoiceInput = {
  readonly text: string;
  readonly is_correct: boolean;
};

export type QuestionInput = {
  readonly text: string;
  readonly difficulty: Difficulty;
  readonly explanation: string;
  readonly era: number;
  readonly topics: ReadonlyArray<number>;
  readonly choices: ReadonlyArray<ChoiceInput>;
};

export type AttemptAnswer = {
  readonly question: number | null;
  readonly question_text: string;
  readonly chosen_text: string;
  readonly correct_text: string;
  readonly is_correct: boolean;
  readonly explanation: string;
};

export type Attempt = {
  readonly id: number;
  readonly era_name: string | null;
  readonly topic_name: string | null;
  readonly score: number;
  readonly total: number;
  readonly percent: number;
  readonly created_at: string;
  readonly answers: ReadonlyArray<AttemptAnswer>;
};

export type AnswerInput = {
  readonly question: number;
  readonly choice: number | null;
};

export type AttemptInput = {
  readonly era?: number;
  readonly topic?: number;
  readonly answers: ReadonlyArray<AnswerInput>;
};

export type QuizFilters = {
  readonly era?: number;
  readonly topic?: number;
  readonly count: number;
};

export type LeaderboardRow = {
  readonly rank: number;
  readonly username: string;
  readonly favorite_club: string;
  readonly attempts: number;
  readonly total_correct: number;
  readonly best_score_pct: number;
};
