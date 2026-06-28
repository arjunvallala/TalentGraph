import type { DemoData } from '../store/appStore';
import type { CandidateResult, CouncilVote, ExplanationData, WorkExperience } from '../lib/api';

// ─── Realistic demo data ─────────────────────────────────────────────────────

const DEMO_JOB_ID = 'demo-job-sde2-2024';

const indianNames = [
  'Arjun Sharma', 'Priya Patel', 'Rahul Kumar', 'Ananya Iyer', 'Vikram Singh',
  'Deepika Nair', 'Rohan Mehta', 'Kavya Reddy', 'Aditya Gupta', 'Sneha Joshi',
  'Kiran Verma', 'Pooja Krishnamurthy', 'Sanjay Bose', 'Meera Pillai', 'Nikhil Thakur',
  'Ritika Agarwal', 'Suresh Chandrasekaran', 'Anjali Mishra', 'Vivek Menon', 'Divya Saxena',
];

const titles = [
  'Senior Software Engineer', 'Full Stack Developer', 'Backend Engineer',
  'Lead Software Engineer', 'Software Engineer II', 'Principal Engineer',
  'Tech Lead', 'Engineering Manager', 'Staff Engineer', 'Senior SDE',
  'Platform Engineer', 'DevOps Engineer', 'Cloud Architect', 'ML Engineer',
  'Data Engineer', 'Solutions Architect', 'Software Developer', 'Senior Developer',
  'Application Engineer', 'Systems Engineer',
];

const companies = [
  'Infosys', 'TCS', 'Wipro', 'HCL Technologies', 'Tech Mahindra',
  'Flipkart', 'Swiggy', 'Zomato', 'CRED', 'Razorpay',
  'Ola', 'Paytm', 'Freshworks', 'Zoho', 'MakeMyTrip',
  'PhonePe', 'PolicyBazaar', 'Nykaa', 'Byju\'s', 'Lenskart',
];

const skillSets: string[][] = [
  ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes', 'AWS'],
  ['React', 'TypeScript', 'Node.js', 'GraphQL', 'MongoDB', 'Redis', 'Docker', 'CI/CD'],
  ['Java', 'Spring Boot', 'Microservices', 'Kafka', 'MySQL', 'AWS', 'Jenkins'],
  ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'SQL', 'Spark'],
  ['Go', 'gRPC', 'Kubernetes', 'Terraform', 'Prometheus', 'Grafana', 'Linux'],
  ['Scala', 'Apache Spark', 'Kafka', 'Hadoop', 'Hive', 'Airflow', 'AWS EMR'],
  ['C++', 'System Design', 'Linux', 'Networking', 'TCP/IP', 'Performance Tuning'],
  ['React Native', 'iOS', 'Swift', 'Android', 'Kotlin', 'Firebase', 'REST APIs'],
];

const recommendations = ['Strong Hire', 'Hire', 'Hire', 'Consider', 'Consider', 'Pass'];
const riskLevels = ['Low', 'Low', 'Medium', 'Medium', 'High'];
const locations = ['Bangalore', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai', 'Delhi', 'Noida', 'Gurgaon'];

function randomBetween(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateCouncilVotes(score: number): CouncilVote[] {
  const councils = [
    { name: 'Technical Depth Council', icon: '🔬' },
    { name: 'Career Trajectory Council', icon: '📈' },
    { name: 'Domain Expertise Council', icon: '🎯' },
    { name: 'Leadership & Impact Council', icon: '🚀' },
    { name: 'Culture Fit Council', icon: '🤝' },
  ];

  return councils.map((c, i) => {
    const variation = (seededRandom(score * 100 + i) - 0.5) * 0.2;
    const councilScore = Math.max(0.1, Math.min(1.0, score + variation));
    const confidence = 0.6 + seededRandom(score * 50 + i) * 0.35;

    return {
      council_name: c.name,
      score: councilScore,
      confidence,
      strengths: [
        `Strong ${i === 0 ? 'technical' : i === 1 ? 'career' : 'domain'} background`,
        `Demonstrated expertise in relevant technologies`,
        `Consistent track record of delivery`,
      ].slice(0, 2),
      concerns: [
        councilScore < 0.7 ? 'Limited experience with required stack' : 'Minor skill gap in cloud services',
        councilScore < 0.6 ? 'Career progression slower than expected' : 'Could benefit from more leadership experience',
      ].slice(0, councilScore < 0.65 ? 2 : 1),
      reasoning: `Based on profile analysis, this candidate shows ${councilScore >= 0.75 ? 'strong' : councilScore >= 0.55 ? 'moderate' : 'weak'} alignment with job requirements.`,
    };
  });
}

function generateExplanation(score: number, name: string, recommendation: string): ExplanationData {
  const isStrong = score >= 0.80;
  const isWeak = score < 0.60;

  return {
    narrative: isStrong
      ? `${name} presents as an exceptionally strong candidate for this role. Their technical depth, combined with proven delivery experience and domain expertise, makes them a compelling choice. The committee unanimously agrees that this candidate can contribute from day one.`
      : isWeak
      ? `${name} shows some relevant experience but falls short of the requirements in key areas. While there is potential for growth, the current skill gaps and experience level do not align well with the immediate needs of the role.`
      : `${name} is a solid candidate with good foundational skills and relevant experience. Some areas need further evaluation, but overall the profile shows reasonable alignment with the job requirements.`,
    top_strengths: [
      'Strong technical foundation in core technologies',
      'Consistent career progression with increasing responsibility',
      'Experience with scalable distributed systems',
    ].slice(0, isStrong ? 3 : 2),
    top_concerns: [
      isWeak ? 'Limited hands-on experience with required stack' : 'Some skill gaps in secondary technologies',
      isWeak ? 'Shorter tenure at previous roles raises stability concerns' : 'Limited team leadership experience',
    ].slice(0, isWeak ? 2 : 1),
    counterfactual: `To rank higher, ${name} would benefit from: gaining more hands-on experience with cloud-native architectures, contributing to open source projects, and demonstrating leadership in cross-functional initiatives.`,
    evidence: {
      technical_skills: [
        'Candidate demonstrates proficiency in Python, with 4+ years of production experience',
        'Has worked with microservices architecture at scale (handling 100K+ RPM)',
      ],
      experience: [
        `${Math.floor(randomBetween(3, 10))} years of software development experience`,
        'Previous experience at product companies handling high-traffic systems',
      ],
      domain_match: [
        'Background aligns well with fintech/e-commerce domain requirements',
        'Has delivered features used by millions of end users',
      ],
    },
    feature_contributions: {
      skill_coverage: score * 0.9 + seededRandom(score * 10) * 0.1,
      semantic_similarity: score * 0.85 + seededRandom(score * 20) * 0.15,
      experience_score: score * 0.95 + seededRandom(score * 30) * 0.05,
      domain_match: score * 0.88 + seededRandom(score * 40) * 0.12,
      career_velocity: score * 0.7 + seededRandom(score * 50) * 0.3,
    },
  };
}

function generateWorkHistory(seed: number): WorkExperience[] {
  const numJobs = Math.floor(seededRandom(seed) * 3) + 2;
  const history: WorkExperience[] = [];
  let yearOffset = 0;

  for (let i = 0; i < numJobs; i++) {
    const duration = Math.floor(seededRandom(seed + i * 7) * 30) + 12;
    const company = companies[Math.floor(seededRandom(seed + i * 3) * companies.length)];
    const title = titles[Math.floor(seededRandom(seed + i * 11) * titles.length)];
    history.push({
      company,
      title,
      start_date: `${2024 - yearOffset - Math.floor(duration / 12)}-01`,
      end_date: i === 0 ? 'Present' : `${2024 - yearOffset}-01`,
      duration_months: duration,
      description: `Led development of core ${['backend', 'frontend', 'platform', 'infrastructure'][i % 4]} features`,
      achievements: [
        `Improved system performance by ${20 + Math.floor(seededRandom(seed + i) * 60)}%`,
        `Led a team of ${2 + Math.floor(seededRandom(seed + i * 2) * 8)} engineers`,
      ],
    });
    yearOffset += Math.floor(duration / 12);
  }
  return history;
}

export function generateDemoData(): DemoData {
  const candidates: CandidateResult[] = indianNames.map((name, i) => {
    const seed = i * 13.7;
    const score = 0.45 + seededRandom(seed) * 0.52; // 0.45 - 0.97
    const recIdx = Math.min(
      recommendations.length - 1,
      Math.floor((1 - score) * recommendations.length)
    );
    const recommendation = recommendations[recIdx];
    const riskIdx = Math.floor((1 - score) * riskLevels.length * 0.8);
    const risk_level = riskLevels[Math.min(riskLevels.length - 1, riskIdx)];
    const skillSet = skillSets[i % skillSets.length];
    const location = locations[i % locations.length];
    const yearsExp = 2 + Math.floor(seededRandom(seed * 2) * 12);
    const company = companies[i % companies.length];
    const title = titles[i % titles.length];

    const genome = {
      technical: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 1) - 0.5) * 0.3)),
      career: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 2) - 0.5) * 0.3)),
      domain: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 3) - 0.5) * 0.3)),
      leadership: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 4) - 0.5) * 0.4)),
      learning: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 5) - 0.5) * 0.3)),
      stability: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 6) - 0.5) * 0.35)),
      behavioral: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 7) - 0.5) * 0.3)),
      readiness: Math.max(0.1, Math.min(1, score + (seededRandom(seed + 8) - 0.5) * 0.25)),
    };

    return {
      candidate_id: `cand-${String(i + 1).padStart(3, '0')}`,
      rank: i + 1,
      overall_score: score,
      confidence_score: 0.5 + seededRandom(seed * 3) * 0.45,
      recommendation,
      risk_level,
      percentile: Math.round((1 - i / indianNames.length) * 100),
      stage: score >= 0.75 ? 1 : score >= 0.6 ? 2 : 3,
      genome_scores: genome,
      profile: {
        candidate_id: `cand-${String(i + 1).padStart(3, '0')}`,
        name,
        current_title: title,
        current_company: company,
        location,
        email: `${name.split(' ')[0].toLowerCase()}@email.com`,
        years_of_experience: yearsExp,
        skills: skillSet,
        work_experience: generateWorkHistory(seed),
        education: [
          {
            degree: 'B.Tech',
            institution: ['IIT Delhi', 'IIT Bombay', 'NIT Trichy', 'BITS Pilani', 'VIT Vellore'][i % 5],
            field: 'Computer Science',
            year: 2024 - yearsExp,
          },
        ],
        certifications: seededRandom(seed * 4) > 0.5
          ? ['AWS Solutions Architect', 'Google Cloud Professional'][i % 2 === 0 ? 0 : 1].split(',')
          : [],
      },
      features: {
        candidate_id: `cand-${String(i + 1).padStart(3, '0')}`,
        experience_score: genome.career,
        skill_coverage: genome.technical,
        semantic_similarity: score * 0.9,
        domain_match: genome.domain,
        career_velocity: genome.career * 0.95,
        leadership_score: genome.leadership,
        education_score: 0.5 + seededRandom(seed * 5) * 0.4,
        stability_score: genome.stability,
        certifications_score: seededRandom(seed * 6) > 0.5 ? 0.7 + seededRandom(seed) * 0.3 : 0.3,
        location_match: seededRandom(seed * 7) > 0.3 ? 0.8 + seededRandom(seed) * 0.2 : 0.5,
        availability_score: 0.7 + seededRandom(seed * 8) * 0.3,
      },
      council_votes: generateCouncilVotes(score),
      explanation: generateExplanation(score, name, recommendation),
      risk_flags: {
        employment_gaps: seededRandom(seed * 9) > 0.8,
        frequent_job_changes: score < 0.6 && seededRandom(seed * 10) > 0.7,
        overqualified: score > 0.9 && seededRandom(seed * 11) > 0.8,
        location_mismatch: seededRandom(seed * 12) > 0.85,
        visa_required: seededRandom(seed * 13) > 0.9,
      },
    };
  });

  // Sort by score
  candidates.sort((a, b) => b.overall_score - a.overall_score);
  candidates.forEach((c, i) => {
    c.rank = i + 1;
    c.percentile = Math.round((1 - i / candidates.length) * 100);
  });

  const scoreDistribution: Record<string, number> = {
    '0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0,
  };
  const recDistribution: Record<string, number> = {};
  const riskDistribution: Record<string, number> = {};

  candidates.forEach((c) => {
    const s = c.overall_score;
    if (s < 0.2) scoreDistribution['0.0-0.2']++;
    else if (s < 0.4) scoreDistribution['0.2-0.4']++;
    else if (s < 0.6) scoreDistribution['0.4-0.6']++;
    else if (s < 0.8) scoreDistribution['0.6-0.8']++;
    else scoreDistribution['0.8-1.0']++;

    recDistribution[c.recommendation] = (recDistribution[c.recommendation] || 0) + 1;
    riskDistribution[c.risk_level] = (riskDistribution[c.risk_level] || 0) + 1;
  });

  return {
    jobProfile: {
      job_id: DEMO_JOB_ID,
      title: 'Senior Software Engineer - Platform',
      description: 'We are looking for a Senior Software Engineer to join our Platform team...',
      required_skills: ['Python', 'Go', 'Kubernetes', 'Microservices', 'PostgreSQL', 'Redis'],
      nice_to_have_skills: ['Rust', 'eBPF', 'Service Mesh', 'Observability'],
      must_have: ['5+ years of backend development', 'Distributed systems experience', 'Production system ownership'],
      implicit_expectations: [
        'Self-starter who can work with minimal supervision',
        'Experience with on-call rotations and incident response',
        'Comfortable with ambiguity in a fast-paced environment',
      ],
      red_flags: [
        'Only frontend experience without backend depth',
        'No experience with distributed systems at scale',
        'Short tenures (<1 year) at multiple companies',
      ],
      ideal_persona: 'A pragmatic engineer with 5-8 years of backend experience, strong fundamentals in distributed systems, and a track record of owning and improving production services at scale.',
      domain: 'Platform / Infrastructure',
      seniority_level: 'Senior',
    },
    rankedList: {
      job_id: DEMO_JOB_ID,
      candidates,
      total_processed: 100000,
      processing_time_seconds: 3.42,
    },
    analytics: {
      job_id: DEMO_JOB_ID,
      total_candidates: candidates.length,
      avg_score: candidates.reduce((s, c) => s + c.overall_score, 0) / candidates.length,
      top_score: Math.max(...candidates.map((c) => c.overall_score)),
      score_distribution: scoreDistribution,
      recommendation_distribution: recDistribution,
      risk_distribution: riskDistribution,
      confidence_distribution: { High: 8, Medium: 7, Low: 5 },
      feature_importance: {
        skill_coverage: 0.82,
        semantic_similarity: 0.78,
        experience_score: 0.74,
        domain_match: 0.71,
        career_velocity: 0.65,
        leadership_score: 0.58,
        stability_score: 0.54,
        education_score: 0.48,
        certifications_score: 0.42,
        location_match: 0.38,
      },
      top_skills: {
        Python: 12,
        'Node.js': 10,
        React: 9,
        'Java': 8,
        'Kubernetes': 8,
        'Docker': 11,
        'AWS': 10,
        'PostgreSQL': 9,
        'Redis': 7,
        'TypeScript': 8,
      },
      stage_distribution: { Stage1: 6, Stage2: 8, Stage3: 6 },
    },
  };
}

export const DEMO_JOB_ID_CONST = DEMO_JOB_ID;
