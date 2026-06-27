import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, BookOpen } from 'lucide-react';
import type { ExplanationData } from '../../lib/api';

interface EvidenceLedgerProps {
  explanation?: ExplanationData;
  evidence?: Record<string, string[]>;
  candidateId?: string;
}

export const EvidenceLedger: React.FC<EvidenceLedgerProps> = ({ explanation, evidence: evidenceProp }) => {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());

  const toggleSection = (key: string) => {
    const next = new Set(openSections);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setOpenSections(next);
  };

  const evidence = evidenceProp || explanation?.evidence || {};
  const sections = Object.entries(evidence);

  function formatKey(key: string): string {
    return key
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  if (sections.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-muted-foreground text-sm gap-2">
        <BookOpen className="w-8 h-8 opacity-40" />
        <p>No evidence data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sections.map(([key, evidenceList], i) => {
        const isOpen = openSections.has(key);
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className="border border-white/[0.08] rounded-xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection(key)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.03] transition-colors text-left"
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                <span className="text-sm font-medium text-white">{formatKey(key)}</span>
                <span className="text-xs text-muted-foreground ml-1">
                  ({evidenceList.length} item{evidenceList.length !== 1 ? 's' : ''})
                </span>
              </div>
              {isOpen ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              )}
            </button>

            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-3 pt-1 space-y-2 border-t border-white/[0.06]">
                    {evidenceList.map((e, j) => (
                      <div
                        key={j}
                        className="flex items-start gap-2.5 p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05]"
                      >
                        <span className="text-accent text-xs mt-0.5 flex-shrink-0">"</span>
                        <p className="text-xs text-muted-foreground leading-relaxed">{e}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
};
