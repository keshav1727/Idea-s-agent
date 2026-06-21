import IdeaSection from './IdeaSection';
import ScriptSection from './ScriptSection';
import HookTemplates from './HookTemplates';
import Patterns from './Patterns';
import Trends from './Trends';

export default function GeneratedPage({ ideas, patterns, onGenerated, showToast }) {
  const hasAnything = ideas.instagram_reels || ideas.youtube_videos || ideas.twitter_threads || patterns.viral_hooks;

  if (!hasAnything) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3 pt-6">
        <p className="text-base font-semibold text-gray-500">No ideas yet</p>
        <p className="text-sm text-gray-400 max-w-sm text-center">Run the pipeline first with: python main.py</p>
      </div>
    );
  }

  return (
    <div className="pt-6">
      <IdeaSection title="📸 Instagram Reel Ideas" items={ideas.instagram_reels || []} icon="📸" section="reels" btnLabel="Generate Reel Ideas" onGenerated={onGenerated} showToast={showToast} />
      <IdeaSection title="▶️ YouTube Video Ideas" items={ideas.youtube_videos || []} icon="▶️" section="videos" btnLabel="Generate Video Ideas" onGenerated={onGenerated} showToast={showToast} />
      <IdeaSection title="🐦 Twitter Thread Ideas" items={ideas.twitter_threads || []} icon="🐦" section="threads" btnLabel="Generate Thread Ideas" onGenerated={onGenerated} showToast={showToast} />
      <ScriptSection reelScripts={ideas.reel_scripts || []} videoScripts={ideas.video_scripts || []} onGenerated={onGenerated} showToast={showToast} />
      <HookTemplates hooks={ideas.viral_hooks || []} onGenerated={onGenerated} showToast={showToast} />
      <Trends topics={ideas.trending_web3_topics || []} />
      <Patterns patterns={patterns} />
    </div>
  );
}
