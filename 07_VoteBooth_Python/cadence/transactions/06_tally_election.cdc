/**
    This transaction withdraws all the Ballots currently in storage, counts them computes the tally for a given Election. This transaction uses the ElectionStandard.ElectionAdmin entitlement to access the privileged function used to compute this result. Because I cannot return anything from a transaction, this particular transaction script logs out the electionResults dictionary for the election in question.

    @param electionId (UInt64) The election identifier for the Election whose tally is to be computed.
**/

import BallotStandard from 0xf8d6e0586b0a20c7
import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

transaction(electionId: UInt64) {
    let electionIndexRef: &{VoteBooth.ElectionIndexPublic}
    let electionStoragePath: StoragePath
    let electionRef: auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election

    prepare(signer: auth(ElectionStandard.ElectionAdmin, BorrowValue) &Account) {
        self.electionIndexRef = signer.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at "
            .concat(VoteBooth.electionIndexPublicPath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )

        self.electionStoragePath = self.electionIndexRef.getElectionStoragePath(electionId: electionId) ??
        panic(
            "Unable to get a StoragePath for Election "
            .concat(electionId.toString())
            .concat(" from the ElectionIndexPublic from account ")
            .concat(signer.address.toString())
        )

        self.electionRef = signer.storage.borrow<auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election>(from: self.electionStoragePath) ??
        panic(
            "Unable to get a valid auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election at "
            .concat(self.electionStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )
    }

    execute {
        let electionBallots: @[BallotStandard.Ballot] <- self.electionRef.withdrawBallots()

        self.electionRef.setEncryptedOptions(_ballotsToTally: <- electionBallots)
    }
}